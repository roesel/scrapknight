#!/usr/bin/env python
# -*- coding: utf-8 -

from database import Database
from mtgsdk import Set


class Connector:
    """
    Object dedicated to communicating with the Mtg API via the python MtgSDK.
    """
    debug = True

    def __init__(self):
        """
        """
        self.db = Database()

    def load_editions(self):
        """
        Loads all editions from the API.
        For a SET, mtg api has the following properties:
            # code
            # name
            # gatherer_code
            old_code
            # magic_cards_info_code
            # release_date
            # border
            # type
            # block
            online_only
            booster
            mkm_id
            mkm_name
        We are using the commented ones, but more could be fetched from the API.
        """

        editions = []
        all_sets = Set.all()
        for s in all_sets:
            editions.append([s.code, s.name, s.gatherer_code, s.magic_cards_info_code, s.release_date,
                             s.border, s.type, s.block])
        self.insert_editions(editions)

    def insert_editions(self, editions):
        """
        Truncates `editions2` table, then inserts pairs of (edition_id, edition_name into DB).
        """
        self.db.truncate_table('sdk_editions')

        for edition in editions:
            query = """
                INSERT INTO `sdk_editions`
                    (`code`, `name`, `gatherer_code`, `magic_cards_info_code`, `release_date`, `border`, `type`, `block`)
                VALUES
                    (%s, %s, %s, %s, %s, %s, %s, %s);
                """

            self.db.insert(query, edition)


sdk = Connector()
sdk.load_editions()
