from config_nonflask import config

import mysql.connector

class Database:

    def __init__(self):

        self.cnx = mysql.connector.connect(**config)
        self.cursor = self.cnx.cursor()

    def insert(self, query):
        try:
            self.cursor.execute(query)
            self.cnx.commit()
        except:
            self.cnx.rollback()

    def query(self, query):
        self.cursor.execute(query)

        return self.cursor.fetchall()

    def __del__(self):
        self.cnx.close()
