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

    @property
    def found_all(self):
        return all([card.found for card in self.cards])

    @property
    def no_multicards(self):
        return all([type(card) is Card for card in self.cards])

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
                            card = Multicard([Card(**c, count=count) for c in result])

                        card.found = True
                        break
                    else:
                        card = Card()
                        card.found = False

                card.count = count
                card.name_req = name
                card.edition_req = edition

                self.cards.append(card)

    def print_price_table(self):
        """
        """

        price = 0
        table = []
        footer = []

        header = ["Card title", "Edition", "Count", "PPU [CZK]", "Price [CZK]"]

        for card in self.cards:

            table.append(card.details_table_row())

            if type(card) is Card:
                if card.cost:
                    price += card.multiprice

            elif type(card) is Multicard:
                for c in card:
                    det = c.details_table_row()
                    det['multicard'] = 'item'
                    table.append(det)

        success = self.found_all and self.no_multicards

        if not success:
            footer_text = "Minimum price --"
        else:
            footer_text = "Full price"

        if not self.found_all:
            footer_text += " some cards not found"
            if not self.no_multicards:
                footer_text += " and"
        if not self.no_multicards:
            footer_text += " some cards have duplicates"

        footer.append([footer_text, "", "", "", str(price) + " CZK"])

        return header, table, footer, success

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


    def details_table_row(self):

        costs = np.unique([card.cost for card in self.card_list if card.cost])
        if not costs:
            str_costs = ""
        elif len(costs) == 1:
            str_costs = str(costs[0])
        else:
            str_costs = "{}--{}".format(costs.min(), costs.max())

        return {
            'found': self.found,
            'multicard': 'head',
            'md5': self.md5,
            'row': [
                {'id': "", 'name': self.name},
                {'id': "", 'name': ""},
                str(self.count),
                str_costs,
                ""]}

class Card():

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


    def __init__(self, id=None, name=None, edition_id=None, edition_name=None,
                 manacost=None, md5=None, buy=None, found=True, count=1):
        """
        """
        self.found = found
        self.id = id
        self.name = name
        self.edition_id = edition_id
        self.edition_name = edition_name
        self.manacost = manacost
        self.md5 = md5
        self.cost = buy
        self.count = count

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

    @property
    def multiprice(self):
        if self.cost:
            return self.count * self.cost
        else:
            return None


    def details_table_row(self):

        det = {
            'found': self.found,
            'multicard': False,
            'md5': self.md5,
            'row': []
        }

        if self.found:
            det['row'] = [
                    {'id': self.id.replace('_', '/'), 'name': self.name},
                    {'id': self.edition_id, 'name': self.edition_name},
                    str(self.count),
                    str(self.cost),
                    str(self.multiprice)]

        else:
            det['not_found_reason'] = Card.not_found_reason(self.name_req, self.edition_req)

            det['row'] = [
                    {'id': 'NotFound', 'name': self.name_req},  # tady bacha na nejaky user injection
                    {'id': self.edition_req, 'name': self.edition_req},
                    str(self.count),
                    '?',
                    '?']

        return det
