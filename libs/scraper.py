#!/usr/bin/env python
# -*- coding: utf-8 -

import re
import numpy as np
import urllib.request
import time
import hashlib
from datetime import datetime

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

    def rebuild_db(self):
        """ Truncates all tables, then rebuilds them. """
        self.empty_db()
        editions = self.get_edition_list()
        self.insert_editions(editions)
        self.update_build_time()
        for edition, edition_name in editions[2:6]:
            log.info("[{}] Starting to scrape edition {}.".format(edition, edition_name))
            cards = self.scrape_edition(edition, sleep=0.5)
            cards = self.format_cards(cards)
            log.info('[{}] {} cards left after cleaning. Inserting into database.'.format(
                edition, str(len(cards))))
            self.insert_cards(cards)
        log.info('Done.')

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
        Inserts pairs of (edition_id, edition_name into DB). Assumes that
        table `editions` is empty.
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
            log.info("(~) There were {} duplicates in edition list. Probs OK. ".format(duplicates))

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

    def format_cards(self, cards):
        """
        Filters scraped cards. Currently only filters played cards, but could filter more in the future.
        Not sure how it handles used foils?
        """
        cards_out = {}
        for card_id, card in cards.items():
            if (self.is_played(card)):
                pass
            else:
                if card_id not in cards_out:
                    cards_out[card_id] = card
                else:
                    log.info('(!) A duplicate entry was attempted, something might be wrong.')

        return cards_out

    def insert_cards(self, cards):
        """
        Inserts dictionary of cards into database, split into `cards` and `costs`.
        """
        for card_id, card in cards.items():
            # Insert into list of cards
            name_md5 = hashlib.md5(card['name'].lower().encode('utf-8')).hexdigest()
            query = """
                INSERT INTO `cards`
                (`id`, `name`, `edition_id`, `manacost`, `md5`)
                VALUES
                (%s, %s, %s, %s, %s)
                """

            self.db.insert(query, (card_id, card['name'], card[
                           'edition'], card['manacost'], name_md5,))

            # Insert into costs
            query = """
                INSERT INTO `costs`
                (`card_id`, `buy`, `buy_foil`)
                VALUES
                (%s, %s, %s)
                """

            self.db.insert(query, (card_id, card['cost'], card['cost_buy_foil'],))

    def empty_db(self):
        """ Calls for truncate of all tables used by Scraper. """

        self.db.insert("SET FOREIGN_KEY_CHECKS=0")
        self.db.truncate_table('editions')
        self.db.truncate_table('cards')
        self.db.truncate_table('costs')
        self.db.insert("SET FOREIGN_KEY_CHECKS=1")

    def get_db_info(self):
        """ Fetches and returns database statistics in the form of a list of strings. """
        print('--- Finished. Statistics: ---')
        query = """SELECT COUNT(*) FROM `cards`;"""
        result = self.db.query(query)
        number_of_cards = result[0][0]

        query = """SELECT COUNT(*) FROM `editions`;"""
        result = self.db.query(query)
        known_editions = result[0][0]

        query = """SELECT COUNT(DISTINCT `edition_id`) FROM `cards`;"""
        result = self.db.query(query)
        number_of_editions = result[0][0]

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

        created = self.get_build_time()

        out = ["Database built on {}.".format(created),
               "{} cards, {} editions out of {} known.".format(
            number_of_cards, number_of_editions, known_editions),
            "Loaded editions: {}.".format(editions),
            "{} normal costs, {} unique.".format(number_of_normal_costs, number_of_unique_costs),
        ]

        return out

    def is_foil(self, card):
        """ Returns if card dictionary item is or isn't foil. """
        return (str.find(card['name'], '- foil') != -1)

    def is_played(self, card):
        """ Returns if card dictionary item is or isn't played. """
        return (str.find(card['name'], '- lightly played') != -1)

    def update_build_time(self):
        """ Inserts current time into the DB as build time into `info`.`created`. """
        dtime = time.strftime('%Y-%m-%d %H:%M:%S')
        query = """
            INSERT INTO info (`key`, `created`) VALUES (1, "{}") ON DUPLICATE KEY UPDATE `created` = "{}";
            """.format(dtime, dtime)
        self.db.insert(query)

    def get_build_time(self):
        """ Returns current build time from DB. """
        query = """SELECT `created` from `info` WHERE `key`=1;"""
        result = self.db.query(query)
        return result[0][0]

    def fetch_url(self, url):
        """
        Downloads HTML contents of a webpage in encoding windows-1250.
        """
        response = urllib.request.urlopen(url)
        data = response.read()              # a `bytes` object
        text = data.decode('windows-1250')  # a `str`; this step can't be used if data is binary
        return text
