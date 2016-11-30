#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import numpy as np
import urllib.request
import time
import warnings
# import MySQLdb


class Database:
    host = 'localhost'
    user = 'root'
    password = ''
    db = 'scrapknight'

    def __init__(self):
        self.connection = MySQLdb.connect(self.host, self.user, self.password, self.db)
        self.cursor = self.connection.cursor()

    def insert(self, query):
        try:
            self.cursor.execute(query)
            self.connection.commit()
        except:
            self.connection.rollback()

    def query(self, query):
        cursor = self.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(query)

        return cursor.fetchall()

    def __del__(self):
        self.connection.close()


class Scraper:
    debug = True
    editions = ["KLD"]

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
                      ' has ' + str(matches[0]) + ' cards.')
            return int(matches[0])
        else:
            warnings.warn('Regex to get # of cards in ' + edition + ' failed.')

    def scrape_edition(self, edition, sleep=0.1):

        # size_of_edition = self.get_edition_size(edition)
        size_of_edition = 100

        cards = []

        for limit in np.arange(0, size_of_edition, 30):
            url = 'http://cernyrytir.cz/index.php3?akce=3&limit=' + \
                str(limit) + '&edice_magic=' + str(edition) + \
                '&poczob=100&foil=R&triditpodle=ceny&hledej_pouze_magic=1&submit=Vyhledej'
            html = self.fetch_url(url)
            matches = re.findall(
                '/images/kusovkymagicsmall/([^.]*).jpg.*?<font style="font-weight : bolder;">([^<]*)</font></div>.*?>(\d*)&nbsp;Kč', html, re.DOTALL)

            if matches:
                cards.append(list(matches[0]))
            else:
                warnings.warn(
                    'A scrape of a page was useless. Not a big deal but probably not correct.')

            time.sleep(sleep)

        if not cards:
            warnings.warn('No cards found in edition ' + edition + '. Something is probably wrong.')
        else:
            if self.debug:
                print(str(len(cards)) + ' cards found in edition ' + edition + '.')
        return cards

    def format_cards(self, cards):
        for card in cards:
            card[0] = card[0].replace('/', '_')

    def insert_into_db(self, cards):
        for card in cards:
            pass

    def run(self):
        matches = []

        for limit in np.arange(0, 30, 30):
            url = 'http://cernyrytir.cz/index.php3?akce=3&limit=' + \
                str(limit) + '&edice_magic=KLD&poczob=100&foil=R&triditpodle=ceny&hledej_pouze_magic=1&submit=Vyhledej'
            response = urllib.request.urlopen(url)
            data = response.read()      # a `bytes` object
            text = data.decode('windows-1250')  # a `str`; this step can't be used if data is binary

            matches3 = re.findall(
                '/images/kusovkymagicsmall/([^.]*).jpg.*?<font style="font-weight : bolder;">([^<]*)</font></div>.*?>(\d*)&nbsp;Kč', text, re.DOTALL)
            # print(matches3)
            matches += matches3

        for card in matches:
            print(card)
    # query = """
    #     INSERT INTO `cards`
    #     (`id`, `name`, `edition`, `manacost`, `cost_buy`, `cost_sell`)
    #     VALUES
    #     ('KLA221', 'Riparian Tiger Bob', 'KLA', '2rr', 15, 35),
    #     ('KLA222', 'Wild Wanderer Mike', 'KLA', '2rw', 5, 3)
    #     """
    #
    # db = Database()
    #
    # db.insert(query)

    # db = {}
    # for a in matches:
    #     if ((str.find(a[0], ' - lightly played') == -1) and (str.find(a[0], '- foil') == -1)):
    #         #print(a[0]+" "+a[1])
    #         db[a[0].lower()] = {'cost': int(a[1]), 'title': a[0]}

    # print(db)

sc = Scraper()
# sc.run()
print(sc.scrape_edition('KLD'))
