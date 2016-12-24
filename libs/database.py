#!/usr/bin/env python
# -*- coding: utf-8 -

import mysql.connector
from mysql.connector import Error, errorcode


class Database:
    debug = False

    def __init__(self, config, debug=False):

        try:
            self.cnx = mysql.connector.connect(**config)
            self.cursor = self.cnx.cursor()
            self.debug = debug

        except Error as err:
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                print("Access denied -- check user name and password in config_db.py")
                raise
            else:
                raise

    def insert(self, query, *args):
        try:
            self.cursor.execute(query, *args)
            self.cnx.commit()

        except Error as err:
            if err.errno == errorcode.ER_BAD_DB_ERROR:
                print("Database does not exist")
                raise
            else:
                raise
            # In any case, roll back (?)
            self.cnx.rollback()

    def query(self, query, *args, **kwargs):
        self.cursor.execute(query, *args, **kwargs)

        return self.cursor.fetchall()

    def __del__(self):
        if hasattr(self, 'cnx'):
            self.cnx.close()

    def truncate_table(self, table):
        """
        Truncates specified table.
        """
        query = """TRUNCATE `scrapknight`.`{}`;""".format(table)
        self.insert(query)
        if self.debug:
            print('Truncated table `{}`.'.format(table))
