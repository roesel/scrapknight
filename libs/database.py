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

    def insert(self, query, *args, **kwargs):
        try:
            self.cursor.execute(query, *args, **kwargs)
            self.cnx.commit()

        except Error as err:
            if err.errno == errorcode.ER_BAD_DB_ERROR:
                print("Database does not exist")
                raise
            else:
                raise
            # In any case, roll back (?)
            self.cnx.rollback()

    def multiinsert(self, query, *args, **kwargs):
        for result in self.cursor.execute(query, *args, **kwargs, multi=True):
            if result.with_rows:
                print("Rows produced by statement '{}':".format(result.statement))
                print(result.fetchall())
            else:
                preview_length = 35
                if len(result.statement) > preview_length:
                    query_preview = ' '.join(result.statement.split())[0:preview_length] + "... ;"
                else:
                    query_preview = result.statement + ";"
                print("Number of rows affected by statement '{}': {}".format(
                    query_preview, result.rowcount))
        self.cnx.commit()

    def multiinsert_simple(self, query, *args, **kwargs):
        for result in self.cursor.execute(query, *args, **kwargs, multi=True):
            if result.with_rows:
                print("Rows produced by statement '{}':".format(result.statement))
                print(result.fetchall())
            else:
                print("Number of rows affected by statement '{}': {}".format(
                    result.statement, result.rowcount))

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
