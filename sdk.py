#!/usr/bin/env python
# -*- coding: utf-8 -

from database import Database
from mtgsdk import Set


class MtgSDKConnector:
    debug = True

    def __init__(self):
        """
        """
        self.db = Database()

    def load_editions(self):
        editions = []
        all_sets = Set.all()
        for s in all_sets:
            editions.append([s.code, s.name])
        self.insert_editions(editions)

    def insert_editions(self, editions):
        """
        Truncates `editions2` table, then inserts pairs of (edition_id, edition_name into DB).
        """
        self.truncate_table('editions2')

        for edition in editions:
            query = """
                INSERT INTO `editions2`
                (`id`, `name`)
                VALUES
                (%s, %s)
                """

            self.db.insert(query, (edition[0], edition[1],))

    def truncate_table(self, table):
        """
        Truncates specified table.
        """
        query = """TRUNCATE `scrapknight`.`{}`;""".format(table)
        self.db.insert(query)
        if self.debug:
            print('Truncated table `{}`.'.format(table))

sdk = MtgSDKConnector()
sdk.load_editions()
