#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import numpy as np
import urllib.request
import time
import warnings
from database import Database
import hashlib


class Scraper:
    debug = True
    editions = []

    def __init__(self):
        self.db = Database()

    def fetch_url(self, url):
        response = urllib.request.urlopen(url)
        data = response.read()              # a `bytes` object
        text = data.decode('windows-1250')  # a `str`; this step can't be used if data is binary
        return text

    def get_edition_size(self, edition):
        html = self.fetch_url(
            'http://cernyrytir.cz/index.php3?akce=3&limit=0&edice_magic=' + edition + '&poczob=30&foil=A&triditpodle=ceny&hledej_pouze_magic=1&submit=Vyhledej')
        matches = re.findall(
            '<td><span class="kusovkytext">Nalezeno (\d*)', html, re.DOTALL)

        if (matches and (matches[0] == matches[1])):
            if self.debug:
                print(str(matches[0]) + ' rows should be available in edition ' + edition + '.')
            return int(matches[0])
        else:
            warnings.warn('Regex to get # of cards in ' + edition + ' failed.')

    def get_edition_list(self):
        html = self.fetch_url('http://cernyrytir.cz/index.php3?akce=3')
        select = re.findall('<select name="edice_magic"(.*?)</select>', html, re.DOTALL)
        matches = re.findall('<option value="([^"]*)" >([^<]*)</option>', select[0], re.DOTALL)

        editions = []
        for match in matches:
            if (match[0] != 'standard') and (match[0] != 'modern'):
                editions.append(match)
                self.editions.append(match[0])
        self.insert_editions(editions)

    def insert_editions(self, editions):

        self.truncate_table('editions')

        for edition in editions:
            query = """
                INSERT INTO `editions`
                (`id`, `name`)
                VALUES
                (%s, %s)
                """

            self.db.insert(query, (edition[0], edition[1],))

    def scrape_edition(self, edition, sleep=0.1):
        size_of_edition = self.get_edition_size(edition)
        cards = {}
        scraped_rows = 0
        for limit in np.arange(0, size_of_edition, 30):
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
                    if manacost == edition.lower():
                        card['manacost'] = "-"
                    else:
                        card['manacost'] = manacost

                    card['cost'] = match[3]

                    # Foil vs non-foil business
                    if card_id in cards:
                        if not self.is_foil(card):
                            foil_cost = cards[card_id]['cost_buy_foil']
                            card['cost_buy_foil'] = foil_cost
                            cards[card_id] = card
                        else:
                            cards[card_id]['cost_buy_foil'] = card['cost']
                    else:
                        if not self.is_foil(card):
                            card['cost_buy_foil'] = 'NULL'
                            cards[card_id] = card
                        else:
                            card['cost_buy_foil'] = card['cost']
                            card['cost'] = 'NULL'
                            card['name'] = card['name'].replace(' - foil', '')
                            cards[card_id] = card

            else:
                warnings.warn(
                    'A scrape of a page was useless. Not a big deal but possibly not correct.')
            time.sleep(sleep)

        if self.debug:
            print(str(scraped_rows) + ' rows scraped in edition ' + edition + '.')

        if not cards:
            warnings.warn('No cards found in edition ' + edition + '. Something is probably wrong.')
        else:
            if self.debug:
                print(str(len(cards)) + ' unique cards found in edition ' + edition + '.')
        return cards

    def format_edition(self, cards):
        # actual ID, completeness, ...
        cards_out = {}

        for card_id, card in cards.items():
            if (self.is_played(card)):
                pass
            else:
                if card_id not in cards_out:
                    cards_out[card_id] = card
                else:
                    warnings.warn(
                        'A duplicate entry was attempted, something might be wrong.')

        return cards_out

    def is_foil(self, card):
        return (str.find(card['name'], '- foil') != -1)

    def is_played(self, card):
        return (str.find(card['name'], '- lightly played') != -1)

    def insert_into_db(self, cards):
        for card_id, card in cards.items():
            # Insert into list of cards
            name_md5 = hashlib.md5(card['name'].lower().encode('utf-8')).hexdigest()
            query = """
                INSERT INTO `cards`
                (`id`, `name`, `edition_id`, `manacost`, `md5`)
                VALUES
                (%s, %s, %s, %s, %s)
                """

            self.db.insert(query, (card_id, card['name'], card['edition'], card['manacost'], name_md5,))

            # Insert into costs
            query = """
                INSERT INTO `costs`
                (`card_id`, `buy`, `buy_foil`)
                VALUES
                (%s, %s, %s)
                """

            self.db.insert(query, (card_id, card['cost'], card['cost_buy_foil'],))

    def empty_db(self):
        self.truncate_table('cards')
        self.truncate_table('costs')
        self.truncate_table('editions')

    def truncate_table(self, table):
        query = """TRUNCATE `scrapknight`.`{}`;""".format(table)
        self.db.insert(query)
        if self.debug:
            print('Truncated table `{}`.'.format(table))

    def rebuild_db(self):
        self.get_edition_list()

        self.empty_db()

        for edition in self.editions[0:9]:
            cards = self.scrape_edition(edition, sleep=0.5)
            cards = self.format_edition(cards)
            if self.debug:
                print(str(len(cards)) + ' cards left after cleaning. Inserting into database.')
            self.insert_into_db(cards)

sc = Scraper()
sc.rebuild_db()
