#!/usr/bin/env python
# -*- coding: utf-8 -

import time
from datetime import datetime

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

    def build(self, editions):
        self.update_build_time()

        self.sc.build(editions)
        self.co.build(editions)

    def scrape(self, editions):
        self.sc.build(editions)

    def connect(self, editions):
        self.co.build(editions)

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

    def update_build_time(self):
        """ Inserts current time into the DB as build time into `info`.`created`. """
        dtime = time.strftime('%Y-%m-%d %H:%M:%S')
        query = """
            INSERT INTO info (`key`, `created`) VALUES (1, "{}") ON DUPLICATE KEY UPDATE `created` = "{}";
            """.format(dtime, dtime)
        self.db.insert(query)

    def get_build_time(self):
        """ Returns current build time from DB. """
        query = """SELECT `created` from `info` WHERE `key`=1;"""
        result = self.db.query(query)
        return result[0][0]

    def get_db_info(self):
        """
        Fetches, combines and returns database statistics in the form of a list of strings.
        """
        info = ["Database built on {}.".format(self.get_build_time())]
        info += self.sc.get_db_info()
        info += self.co.get_db_info()
        return info
