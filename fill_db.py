#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import numpy as np
import urllib.request
import time
import warnings
from database import Database


class Scraper:
    debug = True
    editions = ["KLD", "SOI"]

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
                    card = list(match)
                    card[0] = card[0].replace('/', '_')
                    manacosts = re.findall('/([0-9a-z]*?)\.gif', card[2], re.DOTALL)
                    card[2] = ''.join(manacosts)
                    if card[2] == edition.lower():
                        card[2] = "-"
                    card.append(edition)
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

    def format_edition(self, cards, foil=False, played=False):
        # check for - foil, actual ID, completeness, ...
        cards_out = []
        added_keys = []
        for card in cards:
            if (foil == self.is_foil(card[1])) and (played == self.is_played(card[1])):
                if card[0] not in added_keys:
                    added_keys.append(card[0])
                    cards_out.append(card)
                else:
                    warning.warn('A duplicate entry was attempted, something might be wrong.')

        return cards_out

    def is_foil(self, card):
        return (str.find(card, '- foil') != -1)

    def is_played(self, card):
        return (str.find(card, '- lightly played') != -1)

    def insert_into_db(self, cards):
        for card in cards:
            query = """
                INSERT INTO `cards`
                (`id`, `name`, `edition`, `manacost`, `cost_buy`)
                VALUES
                ('%s', '%s', '%s', '%s', %s)
                """ % (card[0], card[1], card[4], card[2], card[3])

            self.db.insert(query)

    def empty_db(self):
        query = """TRUNCATE `scrapknight`.`cards`;"""
        self.db.insert(query)
        if self.debug:
            print('Truncated table `cards`.')

    def run(self, update=True):
        if update:
            print('Updating database information not implemented.')
        else:
            self.empty_db()

        for edition in self.editions:
            cards = self.scrape_edition(edition, sleep=0.5)
            if self.debug:
                print(str(len(cards)) + ' cards scraped.')
            cards = self.format_edition(cards)
            if self.debug:
                print(str(len(cards)) + ' left after cleaning.')
                self.insert_into_db(cards)

            # db = {}
            # for a in matches:
            #     if ((str.find(a[0], ' - lightly played') == -1) and (str.find(a[0], '- foil') == -1)):
            #         #print(a[0]+" "+a[1])
            #         db[a[0].lower()] = {'cost': int(a[1]), 'title': a[0]}
            #
            # print(db)

sc = Scraper()
sc.run(update=False)
# print(sc.scrape_edition('KLD'))
