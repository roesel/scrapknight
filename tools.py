#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import hashlib
import numpy as np
import urllib.request
import flask
from database import Database

def process(user_input):

    Card.db = Database()

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
                    str(card.name),
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
        self.md5 = hashlib.md5(self.card_id.lower().encode('utf-8')).hexdigest()

        query = """
            SELECT `id`, `name`, `edition`, `manacost`, `cost_buy`
            FROM `cards`
            WHERE md5 = '{}'
            """.format(self.md5)

        result = self.db.query(query)

        if result:
            self.found = True

            self.id, \
            self.name, \
            self.edition, \
            self.manacosts, \
            self.cost = result[0]

        else:
            self.found = False
