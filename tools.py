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
                table.append({
                    'found': card.found,
                    'row': [
                        {'id': card.id.replace('_', '/'), 'name': card.name},
                        {'id': card.edition_id, 'name': card.edition_name},
                        str(card.count),
                        str(card.cost),
                        str(multiprice)]})
                price += multiprice

            else:
                found_all = False
                table.append({
                    'found': card.found,
                    'not_found_reason': card.not_found_reason(),
                    'row': [
                        {'id': 'NotFound', 'name': card.name_req},  # tady bacha na nejaky user injection
                        {'id': card.edition_req, 'name': card.edition_req},
                        str(card.count),
                        '?',
                        '?']})

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
            SELECT `id`, `name`, `edition_id`, `edition_name`, `manacost`, `buy`
            FROM card_details
            WHERE `md5` = '{}'
            """.format(self.md5)

        if self.edition_req:
            ed = self.parse_edition(self.edition_req)

            query += """
            AND `edition_id` = '{}'
            """.format(ed['id'])

        result = self.db.query(query)

        if result:
            self.found = True

            self.id, \
                self.name, \
                self.edition_id, \
                self.edition_name, \
                self.manacosts, \
                self.cost = result[0]

        else:
            self.found = False

    def parse_edition(self, edition):
        """
        In the appliation input, one can specify the edition either by its name
        or by its abbreviation. The syntax is the same, so we don't know what it
        stands for. This function tries both options and returns the edition
        name and its abbreviation as a dictionary.

        Args:
            edition: string specifing the edition.

        returns:
            dictionary with id and name keys specifing the edition.
        """
        # We dont know, if edition is edition id or edition name.
        # Let's assume that these are unique if joined.

        # First try if edition is in fact edition id:
        query = """
            SELECT `name`
            FROM editions
            WHERE `id` = '{}'
            """.format(edition)
        result = self.db.query(query)

        # If so, then return.
        if result:
            return {'id': edition, 'name': result[0]}

        # First try if edition is in fact edition name:
        query = """
            SELECT `id`
            FROM editions
            WHERE `name` = '{}'
            """.format(edition)
        result = self.db.query(query)

        # If so, then return.
        if result:
            return {'id': result[0], 'name': edition}

        # Otherwise return None for both id and name.
        return {'id': None, 'name': None}


    def not_found_reason(self):
        """
        Search for a reson, why a card was not found in the database. These are:
        1) Requested card does not exist.
        2) Requested edition does not exist.
        3) Card name exist, but in different edition than requested.

        We also want to distinguish between cases, where the problem is caused
        by only one of the factors (card name, edition).

        It is worthy to note, that this function assumes, that the card was
        NOT found in the database using the __init__ function.

        Returns:
            reason ... dictionary with text explanation of error reason.
        """

        # Initialize the return value as a dictionary of empty strings.
        reason = {
            'card_name': "",
            'edition': "",
        }

        # First of all, the problem may lie in the edition request
        if self.edition_req:

            # Get edition name and id from unspecified field edition_req
            ed = self.parse_edition(self.edition_req)

            # If the edition record was not found, log it.
            if not ed['id']:
                reason['edition'] = "Eddition {} was not found.".format(self.edition_req)

        # Second problem may be that the does not exist or was found in
        # a different edition. Let's ask for the card details based on its md5.
        query = """
            SELECT `edition_id`
            FROM card_details
            WHERE `md5` = '{}'
            """.format(self.md5)

        result = self.db.query(query)

        # If there is no result, the card name is wrong.
        if not result:
            reason['card_name'] = "Card {} was not found in any edition.".format(self.name_req)

        # Otherwise, there are editions, that contain requested card
        else:
            eds = np.unique(result)  # edditions containing this card

            # Log the reason (appen to previous if applicable).
            if reason['edition']:
                reason['edition'] += " "
            reason['edition'] += "Card {} was found in edition(s) {}.".format(self.name_req, ", ".join(eds))

        return reason
