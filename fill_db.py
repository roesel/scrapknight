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
            'http://cernyrytir.cz/index.php3?akce=3&limit=0&edice_magic=' + edition + '&poczob=30&foil=R&triditpodle=ceny&hledej_pouze_magic=1&submit=Vyhledej')
        matches = re.findall(
            '<td><span class="kusovkytext">Nalezeno (\d*)', html, re.DOTALL)

        if (matches and (matches[0] == matches[1])):
            if self.debug:
                print('Successfully found out edition ' + edition +
                      ' should have ' + str(matches[0]) + ' cards.')
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

        query = """TRUNCATE `scrapknight`.`cards`;"""
        self.db.insert(query)
        if self.debug:
            print('Truncated table `editions`.')

        for edition in editions:
            query = """
                INSERT INTO `editions`
                (`id`, `name`)
                VALUES
                ('%s', '%s')
                """ % (edition[0], edition[1])

            self.db.insert(query)

    def scrape_edition(self, edition, sleep=0.1):
        size_of_edition = self.get_edition_size(edition)
        cards = []

        for limit in np.arange(0, size_of_edition, 30):
            url = 'http://cernyrytir.cz/index.php3?akce=3&limit=' + \
                str(limit) + '&edice_magic=' + str(edition) + \
                '&poczob=100&foil=R&triditpodle=ceny&hledej_pouze_magic=1&submit=Vyhledej'
            html = self.fetch_url(url)
            matches = re.findall(
                '/images/kusovkymagicsmall/([^.]*)\.jpg.*?<font style="font-weight : bolder;">([^<]*)</font></div>.*?(/images/kusovky/.*?\.gif[^&]*).*?>(\d*)&nbsp;Kč', html, re.DOTALL)

            if matches:
                for match in matches:
                    manacosts = re.findall('/([0-9a-z]*?)\.gif', match[2], re.DOTALL)
                    manacost = ''.join(manacosts)

                    card = {}
                    card['id'] = match[0].replace('/', '_')
                    card['name'] = match[1]
                    card['edition'] = edition
                    if manacost == edition.lower():
                        card['manacost'] = "-"
                    else:
                        card['manacost'] = manacost

                    card['cost'] = match[3]

                    cards.append(card)
            else:
                warnings.warn(
                    'A scrape of a page was useless. Not a big deal but probably not correct anyway.')
            time.sleep(sleep)

        if not cards:
            warnings.warn('No cards found in edition ' + edition + '. Something is probably wrong.')
        else:
            if self.debug:
                print(str(len(cards)) + ' cards found in edition ' + edition + '.')
        return cards

    def format_edition(self, cards):
        # check for - foil, actual ID, completeness, ...
        cards_out = []
        added_keys = []
        for card in cards:
            if (self.is_foil(card) == False) and (self.is_played(card) == False):
                if card['id'] not in added_keys:
                    added_keys.append(card['id'])
                    cards_out.append(card)
                else:
                    warnings.warn('A duplicate entry was attempted, something might be wrong.')

        return cards_out

    def is_foil(self, card):
        return (str.find(card['name'], '- foil') != -1)

    def is_played(self, card):
        return (str.find(card['name'], '- lightly played') != -1)

    def insert_into_db(self, cards):
        for card in cards:
            # Insert into list of cards
            name_md5 = hashlib.md5(card['name'].lower().encode('utf-8')).hexdigest()
            query = """
                INSERT INTO `cards`
                (`id`, `name`, `edition`, `manacost`, `md5`)
                VALUES
                ('%s', '%s', '%s', '%s', '%s')
                """ % (card['id'], card['name'], card['edition'], card['manacost'], name_md5)

            self.db.insert(query)

            # Insert into costs
            query = """
                INSERT INTO `costs`
                (`id`, `buy`)
                VALUES
                ('%s', %s)
                """ % (card['id'], card['cost'])

            self.db.insert(query)
            # print(query)

    def empty_db(self):
        query = """TRUNCATE `scrapknight`.`cards`;"""
        self.db.insert(query)
        if self.debug:
            print('Truncated table `cards`.')

    def rebuild_db(self):
        self.get_edition_list()

        self.empty_db()

        for edition in self.editions[0:3]:
            cards = self.scrape_edition(edition, sleep=1)
            if self.debug:
                print(str(len(cards)) + ' cards scraped.')
            cards = self.format_edition(cards)
            if self.debug:
                print(str(len(cards)) + ' left after cleaning.')
                self.insert_into_db(cards)

sc = Scraper()
sc.rebuild_db()
# print(sc.scrape_edition('KLD'))
