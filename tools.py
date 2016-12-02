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

            # Delete newline from string
            row = row.replace(r"\n", "")

            # Get rid of multiple adjoining whitespace.
            row = re.sub(r"\s+", " ", row)

            # Strip leading and trainling whitespace.
            row = row.strip()

            # Check that the row is not a comment
            if len(row) > 0 and not row[0] == '#':

                # If the first character is not a digit, lets assume the
                # number of cards is just ommited and should be equal to 1.
                if not row[0].isdigit():
                    row = '1 x ' + row

                # Regex explained
                # (1) ... one or more digits
                # maybe a whitespace
                # maybe "x"
                # whitespace
                # (2) ... anything but "[", "]" at least once plus anything but "[", "]", or whitespace exactly once
                # maybe a whitespace
                # (3) ... maybe "[" plus maybe anything plus maybe "]"
                #
                # Therefore a string
                # 4 x Inspiring Vantage [KLD]
                # will be split into
                #   count = '4'
                #   name = 'Inspiring Vantage'
                #   edition = '[KLD]'
                #
                match = re.match(
                    r"(\d+)\s?x?\s([^\[\]]+[^\[\]\s])\s?(\[?.*\]?)", row)

                if match:
                    count = int(match.group(1))
                    name = match.group(2)
                    edition = match.group(3).replace("[", "").replace("]", "")

                else:
                    raise ValueError(
                        "Error while processing input row {}: {}".format(i, row))

                # Now get the card instance
                card = Card(name, edition)

                # If card was not found in the database, maybe the problem is
                #  in the wrong apostrophe character.
                if not card.found:
                    name = name.replace("'", "´")
                    card = Card(name, edition)

                card.count = count
                card.user_input = name

                self.cards.append(card)

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
                    {'id': card.id.replace('_', '/'), 'name': card.name},
                    {'id': card.edition, 'name': card.edition_name},
                    str(card.count),
                    str(card.cost),
                    str(multiprice)])
                price += multiprice

            else:
                found_all = False
                table.append([
                    {'id': 'NotFound', 'name': card.name_req},  # tady bacha na nejaky user injection
                    {'id': card.edition_req, 'name': card.edition_req},
                    str(card.count),
                    '?',
                    '?'])

        footer = []

        if not found_all:
            footer.append(["Minimum price - some cards not found", "", "", "", str(price) + " CZK"])
        else:
            footer.append(["Full price", "", "", "",  str(price) + " CZK"])

        header = ["Card title", "Edition", "Count", "PPU [CZK]", "Price [CZK]"]

        return header, table, footer, found_all


class Card():

    def __init__(self, name_req, edition_req=None):
        """
        """

        self.name_req = name_req
        self.edition_req = edition_req.upper()
        self.md5 = hashlib.md5(self.name_req.lower().encode('utf-8')).hexdigest()

        query = """
            SELECT `id`, `name`, `edition`, `edition_name`,`manacost`, `buy`
            FROM (
                SELECT
                cards.id, cards.name, cards.edition, cards.manacost, cards.md5,
                costs.buy, costs.buy_foil,
                editions.name as edition_name
                FROM cards
                INNER JOIN costs ON cards.id = costs.id
                INNER JOIN editions ON cards.edition = editions.id

                ) AS t3
            WHERE `md5` = '{}'
            """.format(self.md5)

        if self.edition_req:
            query += """
            AND `edition` = '{}'
            """.format(self.edition_req)  # zde to chce udelat zase pres md5 a pres join - tabulka karet a tabulka edic s FK -- PK

        result = self.db.query(query)

        if result:
            self.found = True

            self.id, \
                self.name, \
                self.edition, \
                self.edition_name, \
                self.manacosts, \
                self.cost = result[0]

        else:
            self.found = False
