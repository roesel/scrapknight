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
from .card import Card

logging_level = logging.INFO
# logging_level = logging.DEBUG

# Set logging level
logging.basicConfig(
    format='%(levelname)s: %(message)s',
    level=logging_level)

log = logging.getLogger()


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
