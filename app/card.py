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

from multiprocessing.dummy import Pool

pool = Pool(10)

outlog = []

import logging
import pprint

import app.tools

logging_level = logging.INFO
# logging_level = logging.DEBUG

# Set logging level
logging.basicConfig(
    format='%(levelname)s: %(message)s',
    level=logging_level)

log = logging.getLogger()


class Card(object):

    @staticmethod
    def hash_name(name):
        return hashlib.md5(name.lower().encode('utf-8')).hexdigest()

    @classmethod
    def search_by_id(cls, card_id):
        """
        """
        query = """
            SELECT `id`, `cid`, `mid`, `name`, `set_code`, `set_name`,
                `mana_cost`, `layout`, `type`, `rarity`,
                `buy`, `sell`, `buy_foil`, `sell_foil`, `md5`
            FROM sdk_card_details_extended
            WHERE `id` = %s
            """

        result = cls.db.query(query, (card_id,))

        if result:
            keys = ['id', 'cid', 'mid', 'name', 'edition_id', 'edition_name',
                'manacost', 'layout', 'type', 'rarity',
                'buy', 'sell', 'buy_foil', 'sell_foil', 'md5']
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
            SELECT `id`, `cid`, `mid`, `name`, `set_code`, `set_name`,
                `mana_cost`, `layout`, `type`, `rarity`,
                `buy`, `sell`, `buy_foil`, `sell_foil`, `md5`
            FROM sdk_card_details_extended
            WHERE `name` = %s
            """

        if edition_req:
            ed = cls.parse_edition(edition_req)

            query += """
            AND `set_code` = %s
            """

            result = cls.db.query(query, (str(name_req), ed['id'],))
        else:
            result = cls.db.query(query, (str(name_req),))

        if result:
            keys = ['id', 'cid', 'mid', 'name', 'edition_id', 'edition_name',
                'manacost', 'layout', 'type', 'rarity',
                'buy', 'sell', 'buy_foil', 'sell_foil', 'md5']
            return [dict(zip(keys, values)) for values in result]
        else:
            return False

    @classmethod
    def search_similar(cls, name_req, limit=10):
        """
        """
        query = """
            SELECT `id`, `cid`, `mid`, `name`, `set_code`, `set_name`,
                `mana_cost`, `layout`, `type`, `rarity`,
                `buy`, `sell`, `buy_foil`, `sell_foil`, `md5`
            FROM sdk_card_details_extended
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
            keys = ['id', 'cid', 'mid', 'name', 'edition_id', 'edition_name',
                'manacost', 'layout', 'type', 'rarity',
                'buy', 'sell', 'buy_foil', 'sell_foil', 'md5']

            dist = [app.tools.levenshtein(name_req, res[3]) for res in result]
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

    def __init__(self, id=None, cid=None, mid=None,
                 name=None, edition_id=None, edition_name=None,
                 manacost=None, md5=None,
                 buy=None, buy_foil=None, sell=None, sell_foil=None,
                 layout=None,
                 type=None, rarity=None, found=True, count=1,
                 search_hash=None,
                 user=None):
        """
        """
        self.found = found

        self.id = id
        self.mid = mid
        self.cid = cid

        self.name = name
        self.edition_id = edition_id
        self.edition_name = edition_name

        self.manacost = manacost
        self.layout = layout
        self.type = type
        self.rarity = rarity

        self.md5 = md5
        self.cost = buy

        self.count = count
        self.search_hash = search_hash

        if user is not None:
            self.owned = user.owns_card(self)
        else:
            self.owned = False


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

        dist = [app.tools.levenshtein(name, res[0]) for res in result]
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

        if not path.exists():
            log.debug(f'Picture file for card {self.mid} not found.')

            # Download card image, but don't wait for it, rather return the
            # original url. Not sure this is correct (and thread safe, whatever)
            # but it works.
            pool.apply_async(self.download_card_image, [url, str(path)])

            return url
        else:
            log.debug(f'Picture file for card {self.mid} found.')
            return url_for('static', filename='img/cards/' + name)

    @staticmethod
    def download_card_image(url, path):
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
            return re.findall("{([^{}]*)}", mana)
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
                'multiprice': str_multiprice,
                'owned': self.owned}

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
