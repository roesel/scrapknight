#!/usr/bin/env python
# -*- coding: utf-8 -

from mtgsdk import Set
from mtgsdk import Card
import time

from libs.database import Database
from libs.connector import Connector
from libs.scraper import Scraper


class Builder:
    """
    Dedicated to building the DB.
    """
    debug = True
    # self.sc = Scraper()
    # self.co = Connector()

    def __init__(self, db_config):
        """
        """
        self.db = Database(db_config)
        # TODO reconstruct Scraper/Connector to also accept DB objects
        self.sc = Scraper(db_config)
        self.co = Connector(db_config)

    def load_sql(self, filename):
        with open(filename, "rt", encoding='utf-8') as in_file:
            contents = in_file.read()
            statements = contents.split(';')
            for statement in statements:
                self.db.insert(statement)
