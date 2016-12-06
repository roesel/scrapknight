from config_nonflask import config

import mysql.connector


class Database:
    debug = False

    def __init__(self, debug=False):

        self.cnx = mysql.connector.connect(**config)
        self.cursor = self.cnx.cursor()
        self.debug = debug

    def insert(self, query, *args):
        try:
            self.cursor.execute(query, *args)
            self.cnx.commit()
        except:
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
