#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import numpy as np
import urllib.request
import flask

def process(user_input):
    matches = []
    for limit in np.arange(0, 300, 30):
        url = 'http://cernyrytir.cz/index.php3?akce=3&limit='+str(limit)+'&edice_magic=KLD&poczob=100&foil=R&triditpodle=ceny&hledej_pouze_magic=1&submit=Vyhledej'
        response = urllib.request.urlopen(url)
        data = response.read()      # a `bytes` object
        text = data.decode('windows-1250') # a `str`; this step can't be used if data is binary
        #with open('input.txt', 'r', encoding="utf8") as myfile:
        #    data = myfile.read().replace('\n', '')

        matches3 = re.findall('<font style="font-weight : bolder;">([^<]*)</font></div>.*?>(\d*)&nbsp;Kč', text, re.DOTALL)
        #print(matches3)
        matches += matches3

    db = {}
    for a in matches:
        if ((str.find(a[0], ' - lightly played') == -1) and (str.find(a[0], '- foil') == -1)):
            #print(a[0]+" "+a[1])
            db[a[0].lower()] = {'cost': int(a[1]), 'title': a[0]}

    Card.db = db

    mydeck = Deck(user_input)

    return mydeck.print_price_table()


class Deck():

    def __init__(self, user_input):
        """
        """
        self.cards = []

        for i, row in enumerate(user_input.splitlines()):

            split = row.replace('\n', '').split(' x ')

            if not row[0] == '#':
                if len(split) == 2:
                    count = int(split[0])
                    name = split[1]

                    card = Card(name.lower())

                    card.count = count
                    card.user_input = name

                    self.cards.append(card)

                else:
                    raise ValueError(
                        "Error while processing input row {}: {}".format(i, row))

    def print_price_table(self):
        """
        """

        found_all = True
        price = 0
        table = []

        for card in self.cards:

            if card.found:
                multiprice = card.count * card.cost
                table.append([
                    str(card.title),
                    str(card.count),
                    str(card.cost),
                    str(multiprice)])
                price += multiprice

            else:
                found_all = False
                table.append([
                    str(card.user_input), # tady bacha na nejaky user injection
                    str(card.count),
                    '?',
                    '?'])

        footer = []

        if not found_all:
            footer.append(["Minimum price - some cards not found", "", "", str(price) + " CZK"])
        else:
            footer.append(["Full price", "", "",  str(price) + " CZK"])

        header = ["Card title", "Count", "PPU [CZK]", "Price [CZK]"]

        return header, table, footer, found_all

class Card():

    def __init__(self, card_id):
        """
        """

        self.card_id = card_id

        if card_id in self.db:
            self.found = True
            self.cost = self.db[card_id]['cost']
            self.title = self.db[card_id]['title']

        else:
            self.found = False
