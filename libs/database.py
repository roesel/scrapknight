#!/usr/bin/env python
# -*- coding: utf-8 -

import mysql.connector


class Database:
    debug = False

    def __init__(self, config, debug=False):

        self.cnx = mysql.connector.connect(**config)
        self.cursor = self.cnx.cursor()
        self.debug = debug

    def insert(self, query, *args):
        try:
            self.cursor.execute(query, *args)
            self.cnx.commit()
        except mysql.connector.Error as err:
            # Go through possible errors.
            if err.errno == mysql.connector.errorcode.ER_ACCESS_DENIED_ERROR:
                print("Something is wrong with your user name or password")
            elif err.errno == mysql.connector.errorcode.ER_BAD_DB_ERROR:
                print("Database does not exist")
            else:
                print(err)
            # In any case, roll back (?)
            self.cnx.rollback()

    def query(self, query, *args):
        self.cursor.execute(query, *args)

        return self.cursor.fetchall()

    def __del__(self):
        self.cnx.close()

    def truncate_table(self, table):
        """
        Truncates specified table.
        """
        query = """TRUNCATE `scrapknight`.`{}`;""".format(table)
        self.insert(query)
        if self.debug:
            print('Truncated table `{}`.'.format(table))
