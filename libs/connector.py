#!/usr/bin/env python
# -*- coding: utf-8 -

from mtgsdk import Set
from mtgsdk import Card
import time

from libs.database import Database

import logging
import pprint

log = logging.getLogger()


class Connector:
    """
    Object dedicated to communicating with the Mtg API via the python MtgSDK.
    """
    # self.db = Database()

    def __init__(self, db):
        """
        Takes either a Database() object or config sufficient for creating one.
        """
        if isinstance(db, Database):
            self.db = db
        else:
            self.db = Database(db)

    def build_edition_list(self, editions):
        # Build edition list
        self.loaded_editions = self.get_edition_list()
        self.insert_editions(self.loaded_editions)

    def build(self, editions):
        """
        Builds the database to its 'default' state.
        Assumes empty but existing tables.
        """

        # Load all editions from edition list
        for edition in self.loaded_editions:
            edition_code = edition[0]
            if editions is None or edition_code in editions:
                #log.info("Sleeping for 3 seconds...")
                # time.sleep(3)
                log.info("[{}] Loading edition from API...".format(edition_code))
                cards = self.load_edition(edition_code)
                self.insert_cards(cards)
        log.info('Done.')

    def rebuild(self):
        """
        Empties all necessary tables, then builds.
        """
        self.empty_db()
        self.build()

    def get_edition_list(self):
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
        return editions

    def insert_editions(self, editions):
        """
        Truncates `sdk_editions` table, then inserts (edition_id, edition_name, ...) into DB.
        Assumes that table `sdk_editions` is empty.
        """

        for edition in editions:
            query = """
                INSERT INTO `sdk_editions`
                    (`code`, `name`, `gatherer_code`, `magic_cards_info_code`, `release_date`, `border`, `type`, `block`)
                VALUES
                    (%s, %s, %s, %s, %s, %s, %s, %s);
                """

            self.db.insert(query, edition)

    def load_edition(self, edition):
        """
        Loads all cards from a specific edition from the API.
        For a CARD, mtg api has the following properties:

            # name
            # multiverse_id
            layout
            names
            # mana_cost
            cmc
            # colors
            # type
            supertypes
            subtypes
            # rarity
            text
            flavor
            artist
            number
            power
            toughness
            loyalty
            variations
            watermark
            border
            timeshifted
            hand
            life
            reserved
            release_date
            starter
            rulings
            foreign_names
            printings
            original_text
            original_type
            legalities
            source
            image_url
            # set
            set_name
            # id
        """
        all_cards = Card.where(set=edition).all()
        number_of_cards = len(all_cards)

        log.info("[{}] Found {} cards in API. Starting to fetch.".format(edition, number_of_cards))

        cards = []
        for c in all_cards:
            names = None
            if c.names:
                names = " // ".join(c.names)

            cards.append([c.name, names, c.multiverse_id, c.layout,
                          c.mana_cost, c.type, c.rarity, c.set, c.id])

        log.info("[{}] Inserting {} cards into DB.".format(edition, len(cards)))

        return cards

    def insert_cards(self, cards):
        """
        Inserts new values into `sdk_cards`.
        Assumes `sdk_cards` is empty.
        """
        for card in cards:
            query = """
                INSERT INTO `sdk_cards`
                    (`name`, `names`, `mid`, `layout`, `mana_cost`, `type`, `rarity`, `set`, `id`)
                VALUES
                    (%s, %s, %s, %s, %s, %s, %s, %s, %s);
                """
            if card[2] is None:
                log.warning("SDK Fail - multiverseid is None. Card details: {}".format(card))

            log.debug("Inserting card: {}".format(card))
            self.db.insert(query, card)

    def empty_db(self):
        """ Calls for truncate of all tables used by Connector. """

        self.db.insert("SET FOREIGN_KEY_CHECKS=0")
        self.db.truncate_table('sdk_editions')
        self.db.truncate_table('sdk_cards')
        self.db.insert("SET FOREIGN_KEY_CHECKS=1")

    def get_db_info(self):
        """
        Fetches and returns database statistics in the form of a list of strings.
        """
        log.debug('--- Finished. Statistics: ---')
        query = """SELECT COUNT(*) FROM `sdk_cards`;"""
        result = self.db.query(query)
        number_of_cards = result[0][0]

        query = """SELECT COUNT(*) FROM `sdk_editions`;"""
        result = self.db.query(query)
        known_editions = result[0][0]

        query = """SELECT COUNT(DISTINCT `set`) FROM `sdk_cards`;"""
        result = self.db.query(query)
        number_of_editions = result[0][0]

        query = """SELECT DISTINCT `set` from `sdk_cards`;"""
        result = self.db.query(query)
        result_list = [ed[0] for ed in result]
        editions = ','.join(result_list)

        data = {
            'number_of_cards': number_of_cards,
            'number_of_editions': number_of_editions,
            'known_editions': known_editions,
            'editions': editions}

        log.debug(
            "Loaded info:\n"
            "{number_of_cards} cards, {known_editions} editions out of {number_of_editions} known.\n"
            "Loaded editions: {editions}.".format(
                **data))

        return data
