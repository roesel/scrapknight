#!/usr/bin/env python
# -*- coding: utf-8 -

import re
import numpy as np
import urllib.request
import requests
import requests_cache
requests_cache.install_cache('scraper_cache', backend='sqlite', expire_after=60 * 60 * 8)
import time
import hashlib

import mysql.connector
from mysql.connector import Error, errorcode

from libs.database import Database

import logging
import pprint

log = logging.getLogger()


class Scraper:
    """
    Object encapsulating scraping CR eshop, (re)building and checking DB.
    Updating shoud be implemented. Possibly dates of last build per edition.
    """
    # self.db = Database()

    def __init__(self, db):
        """
        Takes either a Database() object or config sufficient for creating one.
        """
        if isinstance(db, Database):
            self.db = db
        else:
            self.db = Database(db)

    def build_edition_list(self, editions):
        # Build edition list
        self.scraped_editions = self.get_edition_list()
        self.insert_editions(self.scraped_editions)

    def build(self, editions):
        """
        Builds the database to its 'default' state.
        Assumes empty but existing tables.
        """
        # Scrape all editions in incoming list
        done = []
        for edition, edition_name in self.scraped_editions:
            if editions is None or edition in editions:
                if edition not in done:
                    log.info("[{}] Starting to scrape edition {}.".format(edition, edition_name))
                    cards = self.scrape_edition(edition, sleep=0.5)
                    cards = self.format_cards(cards)
                    log.info('[{}] {} cards left after cleaning. Inserting into database.'.format(
                        edition, str(len(cards))))
                    self.insert_cards(cards)
                    done.append(edition)
        log.info('Done.')

    def rebuild(self):
        """
        Empties all necessary tables, then builds.
        """
        self.empty_db()
        self.build()

    def get_edition_size(self, edition):
        """
        Looks up number of cards on CR eshop in a specific edition, any foil.
        Expects edition ID like KLD, SOI or M16 and returns int.
        """
        html = self.fetch_url(
            'http://cernyrytir.cz/index.php3?akce=3&limit=0&edice_magic=' + edition + '&poczob=30&foil=A&triditpodle=ceny&hledej_pouze_magic=1&submit=Vyhledej')
        matches = re.findall(
            '<td><span class="kusovkytext">Nalezeno (\d*)', html, re.DOTALL)

        if (matches and (matches[0] == matches[1])):
            log.debug(str(matches[0]) + ' rows should be available in edition ' + edition + '.')
            return int(matches[0])
        else:
            log.info('(!) Regex to get # of cards in ' + edition + ' failed.')

    def get_edition_list(self):
        """
        Looks up the list of all available editions on CR eshop.
        Does not return, inserts into DB instead.
        """
        html = self.fetch_url('http://cernyrytir.cz/index.php3?akce=3')
        select = re.findall('<select name="edice_magic"(.*?)</select>', html, re.DOTALL)
        matches = re.findall('<option value="([^"]*)" >([^<]*)</option>', select[0], re.DOTALL)

        editions = []
        for match in matches:
            if (match[0] != 'standard') and (match[0] != 'modern'):
                editions.append(match)
        return editions

    def insert_editions(self, editions):
        """
        Inserts pairs of (edition_id, edition_name into DB).
        Assumes that table `editions` is empty.
        """
        duplicates = 0
        for edition in editions:
            query = """
                INSERT INTO `editions`
                (`id`, `name`)
                VALUES
                (%s, %s)
                """
            try:
                self.db.insert(query, (edition[0], edition[1],))
            except Error as err:
                if err.errno == errorcode.ER_DUP_ENTRY:
                    log.debug("Edition {} is already in the database, skipping...".format(edition))
                    duplicates += 1
                else:
                    raise
        if duplicates:
            log.info("(~) There were {} duplicates in edition list. Probably OK. ".format(duplicates))

    def scrape_edition(self, edition, sleep=0.1):
        """
        Scrapes CR eshop for all cards in specific edition and takes note of all foil and non-foil costs.
        Keeps card info in a dictionary, future uses might change this to Card() object.
        Sleep tries to be kind to the eshop by sleeping sleep = 0.1 seconds by default between each request.
        """
        size_of_edition = self.get_edition_size(edition)
        cards = {}
        scraped_rows = 0
        for limit in np.arange(0, size_of_edition, 30):  # Assuming pagesize 30
            url = 'http://cernyrytir.cz/index.php3?akce=3&limit=' + \
                str(limit) + '&edice_magic=' + str(edition) + \
                '&poczob=100&foil=A&triditpodle=ceny&hledej_pouze_magic=1&submit=Vyhledej'
            html = self.fetch_url(url)
            matches = re.findall(
                '/images/kusovkymagicsmall/([^.]*)\.jpg.*?<font style="font-weight : bolder;">([^<]*)</font></div>.*?(/images/kusovky/.*?\.gif[^&]*).*?>(\d*)&nbsp;Kč', html, re.DOTALL)

            if matches:
                scraped_rows += len(matches)
                for match in matches:
                    manacosts = re.findall('/([0-9a-z]*?)\.gif', match[2], re.DOTALL)
                    manacost = ''.join(manacosts)

                    card = {}
                    card_id = match[0].replace('/', '_')
                    card['name'] = match[1]
                    card['edition'] = edition
                    # Fixing lands having no manacost
                    if manacost == edition.lower():
                        card['manacost'] = "-"
                    else:
                        card['manacost'] = manacost

                    card['cost'] = match[3]

                    # Foil vs non-foil X existing non-existing
                    # Ignoring played/non-english/strange cards
                    if self.is_normal(card):
                        card_id, card['name'] = self.fix_known_cr_mistakes(card_id, card['name'])

                        if card_id in cards:
                            if not self.is_foil(card):
                                foil_cost = cards[card_id]['cost_buy_foil']
                                card['cost_buy_foil'] = foil_cost
                                cards[card_id] = card
                            else:
                                cards[card_id]['cost_buy_foil'] = card['cost']
                        else:
                            if not self.is_foil(card):
                                card['cost_buy_foil'] = None
                                cards[card_id] = card
                            else:
                                card['cost_buy_foil'] = card['cost']
                                card['cost'] = None
                                card['name'] = card['name'].replace(' - foil', '')
                                cards[card_id] = card

            else:
                log.info('(!) A scrape of a page was useless. Not a big deal but possibly not correct.')
            time.sleep(sleep)

        log.info('[{}] {} rows scraped in edition.'.format(edition, str(scraped_rows)))

        if not cards:
            log.info('[{}] No cards found, something is probably wrong.'.format(edition))
        else:
            log.info('[{}] {} unique cards found.'.format(edition, str(len(cards))))
        return cards

    def fix_known_cr_mistakes(self, card_id, card_name):
        known_id_errors = {
            # ZEN large-graphics lands
            'ZEN_258': 'ZEN_235', 'ZEN_256': 'ZEN_237', 'ZEN_260': 'ZEN_236', 'ZEN_262': 'ZEN_238',  # Forests
            'ZEN_264': 'ZEN_240', 'ZEN_266': 'ZEN_241', 'ZEN_268': 'ZEN_242', 'ZEN_270': 'ZEN_239',  # Islands
            'ZEN_272': 'ZEN_244', 'ZEN_274': 'ZEN_243', 'ZEN_276': 'ZEN_245', 'ZEN_278': 'ZEN_246',  # Mountains
            'ZEN_282': 'ZEN_249', 'ZEN_284': 'ZEN_248', 'ZEN_286': 'ZEN_250', 'ZEN_288': 'ZEN_247',  # Plains
            'ZEN_292': 'ZEN_253', 'ZEN_294': 'ZEN_254', 'ZEN_296': 'ZEN_251', 'ZEN_298': 'ZEN_252',  # Swamps
            # DTK mismatched images fixes
            'DTK_254': 'DTK_133',  # Misthoof Kirin
            'DTK_140': 'DTK_124',  # Center Soul
            # M12 missing images
            'C14_200': 'M12_078',  # Turn to Frog
        }
        if card_id in known_id_errors:
            return known_id_errors[card_id], card_name
        elif card_name == "Scion of Ugin":
            # This is here because Scion of Ugin has a wrong image
            return 'DTK_300', card_name
        else:
            return card_id, card_name

    def format_cards(self, cards):
        """
        Filters scraped cards. Currently only filters played cards, but could filter more in the future.
        Not sure how it handles used foils?
        """
        removals = [" (KLD)", " (AER)"]
        corrections = {
            "Jaces´s Scrutiny": "Jace´s Scrutiny",
            "Berserker´s Onslaught": "Berserkers´ Onslaught",
        }

        cards_out = {}
        for card_id, card in cards.items():
            if card_id not in cards_out:
                old_name = card['name']
                for rem in removals:
                    old_name = old_name.replace(rem, "")
                    card['name'] = old_name
                if old_name in corrections:
                    new_name = corrections[old_name]
                    card['name'] = new_name
                    log.info("(~) Corrected card >{}< to >{}<.".format(old_name, new_name))
                cards_out[card_id] = card
            else:
                log.info('(!) A duplicate entry was attempted, something might be wrong.')

        return cards_out

    def insert_cards(self, cards):
        """
        Inserts dictionary of cards into database, split into `cards` and `costs`.
        """
        duplicates = 0
        duplicates_costs = 0
        for card_id, card in cards.items():
            # Insert into list of cards
            name_md5 = hashlib.md5(card['name'].lower().encode('utf-8')).hexdigest()
            query = """
                INSERT INTO `cards`
                (`id`, `name`, `edition_id`, `manacost`, `md5`)
                VALUES
                (%s, %s, %s, %s, %s)
                """
            try:
                log.debug(
                    "Inserting card:\n{}\n{}\n{}\n{}\n{}\n".format(
                        card_id, card['name'], card['edition'], card['manacost'], name_md5))
                self.db.insert(query, (card_id, card['name'], card[
                    'edition'], card['manacost'], name_md5,))
            except Error as err:
                if err.errno == errorcode.ER_DUP_ENTRY:
                    log.debug(
                        "Card {} is already in the database, skipping...".format(card['name']))
                    duplicates += 1
                else:
                    raise

            # Insert into costs
            query = """
                INSERT INTO `costs`
                (`card_id`, `buy`, `buy_foil`)
                VALUES
                (%s, %s, %s)
                """

            try:
                log.debug(
                    "Inserting card cost:\n{}\n{}\n{}\n".format(
                        card_id, card['cost'], card['cost_buy_foil']))
                self.db.insert(query, (card_id, card['cost'], card['cost_buy_foil'],))
            except Error as err:
                if err.errno == errorcode.ER_DUP_ENTRY:
                    log.debug(
                        "Costs of card {} are already in the database, skipping...".format(card['name']))
                    duplicates_costs += 1
                else:
                    raise
        if duplicates:
            log.info("(~) There were {} duplicates in edition list. Probs OK. ".format(duplicates))
        if duplicates_costs:
            log.info("(~) There were {} duplicates in edition list. Probs OK. ".format(duplicates_costs))

    def empty_db(self):
        """ Calls for truncate of all tables used by Scraper. """

        self.db.insert("SET FOREIGN_KEY_CHECKS=0")
        self.db.truncate_table('editions')
        self.db.truncate_table('cards')
        self.db.truncate_table('costs')
        self.db.insert("SET FOREIGN_KEY_CHECKS=1")

    def get_db_info(self):
        """
        Fetches and returns database statistics in the form of a list of strings.
        """
        log.debug('--- Finished. Statistics: ---')
        query = """SELECT COUNT(*) FROM `cards`;"""
        result = self.db.query(query)
        number_of_cards = result[0][0]

        query = """SELECT COUNT(*) FROM `editions`;"""
        result = self.db.query(query)
        number_of_editions = result[0][0]

        query = """SELECT COUNT(DISTINCT `edition_id`) FROM `cards`;"""
        result = self.db.query(query)
        known_editions = result[0][0]

        query = """SELECT COUNT(`buy`) FROM `costs`;"""
        result = self.db.query(query)
        number_of_normal_costs = result[0][0]

        query = """SELECT COUNT(*) FROM `costs` WHERE `buy` IS NOT NULL OR `buy_foil` IS NOT NULL OR `sell` IS NOT NULL OR `sell_foil` IS NOT NULL;"""
        result = self.db.query(query)
        number_of_unique_costs = result[0][0]

        query = """SELECT DISTINCT `edition_id` from `cards`;"""
        result = self.db.query(query)
        result_list = [ed[0] for ed in result]
        editions = ','.join(result_list)

        data = {
            'number_of_cards': number_of_cards,
            'number_of_editions': number_of_editions,
            'known_editions': known_editions,
            'editions': editions,
            'number_of_normal_costs': number_of_normal_costs,
            'number_of_unique_costs': number_of_unique_costs}

        log.debug(
            "Scraped info:\n"
            "{number_of_cards} cards, {known_editions} editions out of {number_of_editions} known.\n"
            "Scraped editions: {editions}.\n"
            "{number_of_normal_costs} normal costs, {number_of_unique_costs} unique.".format(
                **data))

        return data

    def is_normal(self, card):
        normal = True
        if (str.find(card['name'], '- lightly played') != -1) or \
            (str.find(card['name'], '/ lightly played') != -1) or \
            (str.find(card['name'], '- moderately played') != -1) or \
            (str.find(card['name'], '- heavily played') != -1) or \
            (str.find(card['name'], '- japanese') != -1) or \
            (str.find(card['name'], '- korean') != -1) or \
            (str.find(card['name'], '- chinese') != -1) or \
            (str.find(card['name'], '- russian') != -1) or \
                (str.find(card['name'], '- non-english') != -1):
            normal = False
        return normal

    def is_foil(self, card):
        """ Returns if card dictionary item is or isn't foil. """
        return (str.find(card['name'], '- foil') != -1)

    def get_build_time(self):
        """ Returns current build time from DB. """
        query = """SELECT `created` from `info` WHERE `key`=1;"""
        result = self.db.query(query)
        return result[0][0]

    def fetch_url(self, url):
        """
        Downloads HTML contents of a webpage in encoding windows-1250.
        """
        response = requests.get(url)
        response.encoding = 'windows-1250'
        data = response.text
        return data
