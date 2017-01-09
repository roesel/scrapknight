#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import hashlib
import numpy as np
import random
import urllib.request

import urllib
from pathlib import Path

import mysql.connector
from mysql.connector import Error, errorcode

from libs.database import Database
from app.config import DatabaseConfig

from flask import url_for

outlog = []

import logging
import pprint

# logging_level = logging.INFO
logging_level = logging.DEBUG

# Set logging level
logging.basicConfig(
    format='%(levelname)s: %(message)s',
    level=logging_level)

log = logging.getLogger()


def process(user_input):

    outlog = []

    Card.db = Database(DatabaseConfig)

    mydeck = Deck(user_input=user_input)

    return mydeck.print_price_table()

def print_user_deck(user, deck_id):

    outlog = []

    Card.db = Database(DatabaseConfig)

    mydeck = user.get_deck(deck_id)

    return mydeck.print_price_table()

def print_user_library(user):

    outlog = []

    Card.db = Database(DatabaseConfig)

    mydeck = user.get_library()

    return mydeck.print_price_table()

def users_cards_save(user, user_input):

    outlog = []

    Card.db = Database(DatabaseConfig)

    mydeck = Deck(user_input=user_input)

    user.save_cards(mydeck)

def save_user_library(user, user_input):

    outlog = []

    Card.db = Database(DatabaseConfig)

    mydeck = Deck(user_input=user_input)

    return user.save_library(mydeck)

def modify_user_deck(user, deck_id, user_input):

    outlog = []

    Card.db = Database(DatabaseConfig)

    mydeck = Deck(user_input=user_input)

    return user.save_deck(deck_id, mydeck)

def levenshtein(source, target):
    """
    Source: https://en.wikibooks.org/wiki/Algorithm_Implementation/Strings/Levenshtein_distance#Python
    """
    if len(source) < len(target):
        return levenshtein(target, source)

    # So now we have len(source) >= len(target).
    if len(target) == 0:
        return len(source)

    # We call tuple() to force strings to be used as sequences
    # ('c', 'a', 't', 's') - numpy uses them as values by default.
    source = np.array(tuple(source))
    target = np.array(tuple(target))

    # We use a dynamic programming algorithm, but with the
    # added optimization that we only need the last two rows
    # of the matrix.
    previous_row = np.arange(target.size + 1)
    for s in source:
        # Insertion (target grows longer than source):
        current_row = previous_row + 1

        # Substitution or matching:
        # Target and source items are aligned, and either
        # are different (cost of 1), or are the same (cost of 0).
        current_row[1:] = np.minimum(
            current_row[1:],
            np.add(previous_row[:-1], target != s))

        # Deletion (target grows shorter than source):
        current_row[1:] = np.minimum(
            current_row[1:],
            current_row[0:-1] + 1)

        previous_row = current_row

    return previous_row[-1]

class Deck(object):

    @property
    def found_all(self):
        return all([card.found for card in self.cards])

    @property
    def any_multicards(self):
        return any([type(card) is Multicard for card in self.cards])

    @property
    def found_all_costs(self):
        return all([card.cost_found for card in self.cards])

    def __init__(self, user_input=None, card_list=None):
        """
        """
        self.cards = []

        if user_input is not None:

            log.debug("Processing User input:")

            for i, row in enumerate(user_input.splitlines()):

                # Delete newline from string
                row = row.replace(r"\n", "")

                # Get rid of multiple adjoining whitespace.
                row = re.sub(r"\s+", " ", row)

                # Strip leading and trainling whitespace.
                row = row.strip()

                # Check that the row is not a comment
                if len(row) > 0 and not row[0] == '#':

                    log.debug("  {}: {}".format(i, row))

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
                        outlog.append("Error while processing input row {}: {}".format(i, row))
                        continue
                        raise ValueError(
                            "Error while processing input row {}: {}".format(i, row))

                    search_hash = Card.hash_name(name)

                    # There may a problem with a wrong appostrophe character in the
                    # input. Loop over possible variants, break on first successfull
                    # search.
                    name_variants = np.unique([name, name.replace("'", "´")])

                    card = None

                    for name_var in name_variants:

                        log.debug("  seaching for: {}".format(name_var))

                        # Search for the card.
                        result = Card.search(name_var, edition)

                        log.debug("  result: {}".format(result))

                        if result:
                            # If the result is a single row, there is no problem,
                            # instantiate a Card.
                            if len(result) == 1:
                                card = Card(**result[0], count=count)

                            # If there was more matches (should be only possible if
                            # a card with the same name exist in multiple editios),
                            # instantiate a Multicard. That is basically a list of
                            # Card instances with some special methods.
                            else:
                                card = Multicard(
                                    [Card(**c, count=0, search_hash=search_hash) for c in result])
                                card.multicard_info = "multiple_cards"

                            # Either way, the card was found, so we can break the
                            # search loop.
                            card.found = True
                            break

                    # If the card was not found yet, search for similar names using
                    # fulltext search.
                    if not card:

                        # Prevent db query errors when card name contained "'".
                        # This is somewhat dirty solution...
                        # name = name.replace("'", "´")

                        similar = Card.search_similar(name, limit=None)

                        if similar:
                            card = Multicard(
                                [Card(**c, count=0, search_hash=search_hash) for c in similar])
                            card.found = True
                            card.name = name
                            card.multicard_info = "similar_search"

                        else:
                            # If the result is empty, we instantiate an empty Card.
                            card = Card()
                            card.found = False

                    # Store some requested properties.
                    # card.count = count
                    card.name_req = name
                    card.edition_req = edition
                    card.search_hash = search_hash

                    # Append the card to the deck list.
                    self.cards.append(card)

        elif card_list is not None:
            for i, c in enumerate(card_list):

                card_id = c['id']
                count = int(c['count'])

                # Search for the card.
                result = Card.search_by_id(card_id)

                if result:
                    # If the result is a single row, there is no problem,
                    # instantiate a Card.
                    if len(result) == 1:
                        card = Card(**result[0], count=count)

                    else:
                        raise

                    card.found = True

                else:
                    raise

                # Store some requested properties.
                card.name_req = card.name
                card.edition_req = card.edition_name
                card.search_hash = card.md5

                # Append the card to the deck list.
                self.cards.append(card)

    def print_price_table(self):
        """
        """

        price = 0
        table = []
        footer = []

        columns = ['name', 'manacost', 'edition', 'count', 'count_input', 'price', 'multiprice']
        header_texts = ["Card title", "Manacost", "Edition", "Count", "Count", "PPU [CZK]", "Price [CZK]"]
        header_data_field = ["title", "manacost", "edition", "count", "count", "price", "multiprice"]
        header_data_sortable = [True, True, True, True, True, True, True]
        header_widths = [6, 4, 2, 2, 2, 4, 4]

        header = [(col, {
            'text': text,
            'width': width,
            'data_field': data_field,
            'data_sortable': data_sortable},)
                  for col, text, width, data_field, data_sortable
                  in zip(columns, header_texts, header_widths, header_data_field, header_data_sortable)]

        header = dict(header)

        for card in self.cards:

            details = card.details_table_row()

            table.append(details)

            if type(card) is Card:
                if card.cost:
                    price += card.multiprice

            elif type(card) is Multicard:
                for c in card:
                    det = c.details_table_row()
                    det['multicard'] = 'item'
                    det['multicard_info'] = details['multicard_info']
                    table.append(det)

        success = self.found_all and not self.any_multicards and self.found_all_costs

        if not success:
            footer_text = "Minimum price"
            not_success_reason = []

            if not self.found_all:
                not_success_reason.append("some cards not found")
            if self.any_multicards:
                not_success_reason.append("some cards have duplicates")
            if not self.found_all_costs:
                not_success_reason.append("some prices not found")

            footer_text_2 = u'\u2014' + " "  # u'\u2014' is emdash
            footer_text_2 += " and ".join(not_success_reason)

        else:
            footer_text = "Full price"
            footer_text_2 = ""

        footer.append([footer_text, footer_text_2, str(price)])

        table_data = {
            'header': header,
            'body': table,
            'footer': footer,
            'columns': ['name', 'manacost', 'edition', 'count', 'price', 'multiprice'],
            'success': success}

        return table_data, np.unique(outlog)


class Multicard(object):

    def __init__(self, card_list):
        self.card_list = card_list

    @property
    def name(self):
        try:
            return self._name
        except AttributeError as e:
            return self.card_list[0].name

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def md5(self):
        return self.card_list[0].md5

    @property
    def cost_found(self):
        return all([card.cost_found for card in self.card_list])

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

        if not any(costs):
            str_costs = ""
        elif len(costs) == 1:
            str_costs = str(costs[0])
        else:
            str_costs = str(costs.min()) + " " + u'\u2013' + " " + \
                str(costs.max())  # u'\u2013' is endash

        return {
            'img_url': url_for('static',filename='img/card_back.jpg'),
            'found': self.found,
            'multicard': 'head',
            'md5': self.md5,
            'search_hash': self.search_hash,
            'multicard_info': self.multicard_info,
            'card_id': "",
            'name': self.name,
            'manacost': '',
            'edition_id': "",
            'edition_name': "",
            'count': "",  # str(self.count),
            'price': str_costs,
            'multiprice': ""}


class Card(object):

    @staticmethod
    def hash_name(name):
        return hashlib.md5(name.lower().encode('utf-8')).hexdigest()

    @classmethod
    def search_by_id(cls, card_id):
        """
        """
        query = """
            SELECT `id`, `name`, `edition_id`, `edition_name`, `manacost`,
                `buy`, `sell`, `buy_foil`, `sell_foil`, `md5`,
                `mid`, `layout`, `type`, `rarity`
            FROM card_details_extended
            WHERE `id` = %s
            """

        result = cls.db.query(query, (card_id,))

        if result:
            keys = ['id', 'name', 'edition_id', 'edition_name', 'manacost',
                'buy', 'sell', 'buy_foil', 'sell_foil', 'md5',
                'mid', 'layout', 'type', 'rarity']
            return [dict(zip(keys, values)) for values in result]
        else:
            return False

    @classmethod
    def search(cls, name_req, edition_req=None):
        """
        """
        edition_req = edition_req.upper()
        md5 = cls.hash_name(name_req)

        query = """
            SELECT `id`, `name`, `edition_id`, `edition_name`, `manacost`,
                `buy`, `sell`, `buy_foil`, `sell_foil`, `md5`,
                `mid`, `layout`, `type`, `rarity`
            FROM card_details_extended
            WHERE `md5` = %s
            """

        if edition_req:
            ed = cls.parse_edition(edition_req)

            query += """
            AND `edition_id` = %s
            """

            result = cls.db.query(query, (md5, ed['id'],))
        else:
            result = cls.db.query(query, (md5,))

        if result:
            keys = ['id', 'name', 'edition_id', 'edition_name', 'manacost',
                'buy', 'sell', 'buy_foil', 'sell_foil', 'md5',
                'mid', 'layout', 'type', 'rarity']
            return [dict(zip(keys, values)) for values in result]
        else:
            return False

    @classmethod
    def search_similar(cls, name_req, limit=10):
        """
        """
        query = """
            SELECT `id`, `name`, `edition_id`, `edition_name`, `manacost`,
                `buy`, `sell`, `buy_foil`, `sell_foil`, `md5`,
                `mid`, `layout`, `type`, `rarity`
            FROM card_details_extended
            WHERE MATCH (`name`)
            AGAINST (%s IN BOOLEAN MODE)
            """

        if limit:
            query += """
            LIMIT %s
            """
            result = cls.db.query(query, (name_req + "*", limit,))
        else:
            result = cls.db.query(query, (name_req + "*",))

        if result:
            keys = ['id', 'name', 'edition_id', 'edition_name', 'manacost',
                'buy', 'sell', 'buy_foil', 'sell_foil', 'md5',
                'mid', 'layout', 'type', 'rarity']

            dist = [levenshtein(name_req, res[1]) for res in result]
            sorted_idx = np.argsort(dist)

            sorted_result = [result[idx] for idx in sorted_idx]

            return [dict(zip(keys, values)) for values in sorted_result]
        else:
            return False

    @property
    def cost_found(self):
        if self.cost is not None:
            return True
        else:
            return False

    def __init__(self, id=None, name=None, edition_id=None, edition_name=None,
                 manacost=None, md5=None,
                 buy=None, buy_foil=None, sell=None, sell_foil=None,
                 mid=None, layout=None,
                 type=None, rarity=None, found=True, count=1,
                 search_hash=None):
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
        self.mid = mid
        self.layout = layout
        self.type = type
        self.rarity = rarity
        self.count = count
        self.search_hash = search_hash

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
            WHERE `id` = %s
            """
        result = cls.db.query(query, (edition,))

        # If so, then return.
        if result:
            return {'id': edition, 'name': result[0]}

        # First try if edition is in fact edition name:
        query = """
            SELECT `id`
            FROM editions
            WHERE `name` = %s
            """
        result = cls.db.query(query, (edition,))

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
            WHERE `md5` = %s
            """

        result = cls.db.query(query, (md5,))

        # If there is no result, the card name is wrong.
        if not result:
            reason['card_name'] = "Card {} was not found in any edition.".format(name_req)

            similar = Card.match_name(name_req)
            if similar:
                reason['card_name'] += "Similar cards found: " + ", ".join(similar)

        # Otherwise, there are editions, that contain requested card
        else:
            eds = np.unique(result)  # edditions containing this card

            # Log the reason (appen to previous if applicable).
            if reason['edition']:
                reason['edition'] += " "
            reason[
                'edition'] += "Card {} was found in edition(s) {}.".format(name_req, ", ".join(eds))

        return reason

    @classmethod
    def match_name(cls, name, limit=10):
        """
        """

        query = """
            SELECT `name` FROM `card_details`
            WHERE MATCH (`name`)
            AGAINST (%s IN BOOLEAN MODE)
            LIMIT %s
            """

        result = cls.db.query(query, (name, limit,))

        dist = [levenshtein(name, res[0]) for res in result]
        sorted_idx = np.argsort(dist)

        sorted_result = [result[idx][0] for idx in sorted_idx]

        return sorted_result

    @property
    def multiprice(self):
        if self.cost:
            return self.count * self.cost
        else:
            return None

    @property
    def img_url(self):
        if self.mid is not None:
            name = str(self.mid) + '.png'
            url_name = str(self.mid) + '.jpg'
            url = 'https://image.deckbrew.com/mtg/multiverseid/' + url_name
        elif self.cid is not None:
            name = self.cid + '.jpg',
            url_name = self.cid.replace('_', '/') + '.jpg',
            url = 'http://cernyrytir.cz/images/kusovkymagic/' + url_name
        else:
            return url_for('static',filename='img/card_back.jpg')

        directory = Path('app/static/img/cards/')
        directory.mkdir(exist_ok=True)
        path = directory / name

        if path.exists():
            return url_for('static', filename='img/cards/' + name)
        else:
            try:
                urllib.request.urlretrieve(url, str(path))
                return url_for('static', filename='img/cards/' + name)
            except urllib.error.URLError as e:
                ResponseData = e.read().decode("utf8", 'ignore')
                outlog.append(ResponseData)
                return url

    @property
    def manacost_parsed(self):
        if self.manacost is not None:
            mana = self.manacost.replace('/', '')
            return re.findall("{(.*?)}", mana)
        else:
            return None

    def details_table_row(self):

        det = {
            'found': self.found,
            'multicard': False,
            'md5': self.md5,
            'card_id': self.id,
            'search_hash': self.search_hash,
        }

        if self.found:
            if self.cost:
                str_cost = str(self.cost)
            else:
                str_cost = ""

            if self.multiprice:
                str_multiprice = str(self.multiprice)
            else:
                str_multiprice = ""

            addet = {
                'img_url': self.img_url,
                'name': self.name,
                'manacost': self.manacost_parsed,
                'edition_name': self.edition_name,
                'edition_id': self.edition_id,
                'count': str(self.count),
                'price': str_cost,
                'multiprice': str_multiprice}

        else:
            addet = {
                'not_found_reason': Card.not_found_reason(self.name_req, self.edition_req),
                'img_url': url_for('static', filename='img/card_back.jpg'),
                'name': self.name_req,  # tady bacha na nejaky user injection
                'manacost': '',
                'edition_name': self.edition_req,
                'edition_id': None,
                'count': str(self.count),
                'price': '',
                'multiprice': ''}

        return {**det, **addet}
