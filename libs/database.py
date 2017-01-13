#!/usr/bin/env python
# -*- coding: utf-8 -

import mysql.connector
from mysql.connector import Error, errorcode

import logging
import pprint

log = logging.getLogger()


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
            insert_id = self.cursor.lastrowid
            self.cnx.commit()
            return insert_id

        except Error as err:
            if err.errno == errorcode.ER_BAD_DB_ERROR:
                print("Database does not exist")
                raise
            else:
                raise
            # In any case, roll back (?)
            self.cnx.rollback()

    def multiinsert(self, query, *args, **kwargs):
        """
        WORKAROUND for correct reporting of changed rows is not ideal.
        """
        i = 0
        statements = ""
        changed_rows = 0
        for result in self.cursor.execute(query, *args, **kwargs, multi=True):
            if result.with_rows:
                print("Rows produced by statement '{}':".format(result.statement))
                print(result.fetchall())
            else:
                preview_length = 35
                if i == 0:
                    statements = result.statement.split(";")
                if len(statements[i]) > preview_length:
                    query_preview = ' '.join(statements[i].split())[0:preview_length] + "...;"
                else:
                    query_preview = statements[i][0:-1] + ";"
                log.debug("Number of rows affected by statement '{}': {}".format(
                    query_preview, result.rowcount))
                changed_rows += result.rowcount
                i += 1
        self.cnx.commit()
        return changed_rows

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
