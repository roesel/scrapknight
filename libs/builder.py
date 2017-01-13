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

        scrape_start = time.time()
        self.sc.build(editions)
        scrape_took = time.time() - scrape_start

        connect_start = time.time()
        self.co.build(editions)
        connect_took = time.time() - connect_start

        log.info("Scraping took {}.".format(self.readable_time(scrape_took)))
        log.info("Connecting took {}.".format(self.readable_time(connect_took)))

    def readable_time(self, seconds):
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        return "%d:%02d:%02d" % (h, m, s)

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
        info = {
            'db_built_time': self.get_build_time(),
            'scrapper': self.sc.get_db_info(),
            'connector': self.co.get_db_info()}
        return info
