#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import hashlib
import numpy as np
import urllib.request
import flask
from database import Database


def process(user_input):

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

                # If card was not found in the database, maybe the problem is
                #  in the wrong apostrophe character.
                name_variants = [name, name.replace("'", "´")]

                for name_var in name_variants:
                    # Now get the card instance
                    result = Card.search(name_var, edition)
                    if result:
                        print(result)
                        if len(result) == 1:
                            card = Card(**result[0])
                        else:
                            card = Multicard([Card(**c) for c in result])

                        card.found = True
                        break
                    else:
                        card = Multicard([])
                        card.found = False

                card.count = count
                card.name_req = name
                card.edition_req = edition

                self.cards.append(card)

    def print_price_table(self):
        """
        """

        found_all = True
        price = 0
        table = []

        for card in self.cards:

            if card.found:

                if type(card) is Card:

                    if card.cost:
                        multiprice = card.count * card.cost
                        price += multiprice
                    else:
                        found_all = False
                        multiprice = "?"

                    table.append({
                        'found': card.found,
                        'multicard': False,
                        'row': [
                            {'id': card.id.replace('_', '/'), 'name': card.name},
                            {'id': card.edition_id, 'name': card.edition_name},
                            str(card.count),
                            str(card.cost),
                            str(multiprice)]})

                elif type(card) is Multicard:

                    found_all = False
                    multiprice = "?"

                    table.append({
                        'found': card.found,
                        'multicard': 'head',
                        'md5': card.md5,
                        'row': [
                            {'id': "", 'name': card.name},
                            {'id': "", 'name': ""},
                            str(card.count),
                            "",
                            ""]})

                    for c in card:
                        if c.cost:
                            multiprice = card.count * c.cost
                        else:
                            multiprice = "?"

                        table.append({
                            'found': c.found,
                            'multicard': 'item',
                            'md5': c.md5,
                            'row': [
                                {'id': c.id.replace('_', '/'), 'name': c.name},
                                {'id': c.edition_id, 'name': c.edition_name},
                                str(card.count),
                                str(c.cost),
                                str(multiprice)]})

            else:
                found_all = False
                table.append({
                    'found': card.found,
                    'multicard': False,
                    'not_found_reason': Card.not_found_reason(card.name_req, card.edition_req),
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

        print(table)

        return header, table, footer, found_all

class Multicard():

    def __init__(self, card_list):
        self.card_list = card_list

    @property
    def name(self):
        return self.card_list[0].name

    @property
    def md5(self):
        return self.card_list[0].md5

    def __iter__(self):
        self._iter_current = 0
        return self

    def __next__(self):
        if self._iter_current < len(self.card_list):
            self._iter_current += 1
            return self.card_list[self._iter_current - 1]
        else:
            raise StopIteration

class Card():

    db = Database()

    @staticmethod
    def hash_name(name):
        return hashlib.md5(name.lower().encode('utf-8')).hexdigest()


    @classmethod
    def search(cls, name_req, edition_req=None):
        """
        """
        edition_req = edition_req.upper()
        md5 = cls.hash_name(name_req)

        query = """
            SELECT `id`, `name`, `edition_id`, `edition_name`, `manacost`, `md5`, `buy`
            FROM card_details
            WHERE `md5` = '{}'
            """.format(md5)

        if edition_req:
            ed = cls.parse_edition(edition_req)

            query += """
            AND `edition_id` = '{}'
            """.format(ed['id'])

        result = cls.db.query(query)

        if result:
            keys = ['id', 'name', 'edition_id', 'edition_name', 'manacost', 'md5', 'buy']
            return [dict(zip(keys, values)) for values in result]
        else:
            return False


    def __init__(self, id, name, edition_id, edition_name, manacost, md5, buy=None):
        """
        """
        self.found = True
        self.id = id
        self.name = name
        self.edition_id = edition_id
        self.edition_name = edition_name
        self.manacost = manacost
        self.md5 = md5
        self.cost = buy

    @classmethod
    def parse_edition(cls, edition):
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
        result = cls.db.query(query)

        # If so, then return.
        if result:
            return {'id': edition, 'name': result[0]}

        # First try if edition is in fact edition name:
        query = """
            SELECT `id`
            FROM editions
            WHERE `name` = '{}'
            """.format(edition)
        result = cls.db.query(query)

        # If so, then return.
        if result:
            return {'id': result[0], 'name': edition}

        # Otherwise return None for both id and name.
        return {'id': None, 'name': None}

    @classmethod
    def not_found_reason(cls, name_req, edition_req=None):
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

        md5 = cls.hash_name(name_req)

        # First of all, the problem may lie in the edition request
        if edition_req:

            # Get edition name and id from unspecified field edition_req
            ed = cls.parse_edition(edition_req)

            # If the edition record was not found, log it.
            if not ed['id']:
                reason['edition'] = "Eddition {} was not found.".format(edition_req)

        # Second problem may be that the does not exist or was found in
        # a different edition. Let's ask for the card details based on its md5.
        query = """
            SELECT `edition_id`
            FROM card_details
            WHERE `md5` = '{}'
            """.format(md5)

        result = cls.db.query(query)

        # If there is no result, the card name is wrong.
        if not result:
            reason['card_name'] = "Card {} was not found in any edition.".format(name_req)

        # Otherwise, there are editions, that contain requested card
        else:
            eds = np.unique(result)  # edditions containing this card

            # Log the reason (appen to previous if applicable).
            if reason['edition']:
                reason['edition'] += " "
            reason['edition'] += "Card {} was found in edition(s) {}.".format(name_req, ", ".join(eds))

        return reason
