#!/usr/bin/env python
# -*- coding: utf-8 -

from mtgsdk import Set
from mtgsdk import Card
import time

from libs.database import Database
from libs.connector import Connector
from libs.scraper import Scraper

import logging
import pprint

log = logging.getLogger()


class Builder:
    """
    Dedicated to building the DB, mostly by calling Scraper/Connector.
    """
    # self.sc = Scraper()
    # self.co = Connector()
    # self.db = Database()

    def __init__(self, db_config):
        """
        Creates a Database() object and passes it to Scraper/Connector upon creation.
        """
        self.db = Database(db_config)
        self.sc = Scraper(self.db)
        self.co = Connector(self.db)

    def load_sql(self, filename):
        with open(filename, "rt", encoding='utf-8') as in_file:
            contents = in_file.read()
            statements = contents.split(';')
            for statement in statements:

                # trim whitespace
                statement = statement.strip()

                if statement is not "":
                    log.debug("executing SQL statement:\n+++{}+++".format(statement))
                    self.db.insert(statement)

    def scrape(self):
        self.sc.rebuild()

    def connect(self):
        self.co.rebuild()
