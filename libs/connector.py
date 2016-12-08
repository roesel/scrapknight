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

    def build(self):
        """
        Builds the database to its 'default' state.
        Assumes empty but existing tables.
        """
        editions = self.get_edition_list()
        self.insert_editions(editions)

        list_of_editions = ['KLD', 'SOI', 'BFZ']
        for e in list_of_editions:
            log.info("Sleeping for 5 seconds...")
            time.sleep(5)
            log.info("[{}] Loading edition from API...".format(e))
            cards = self.load_edition(e)
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
            cards.append([c.name, c.multiverse_id, c.layout,
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
                    (`name`, `mid`, `layout`, `mana_cost`, `type`, `rarity`, `set`, `id`)
                VALUES
                    (%s, %s, %s, %s, %s, %s, %s, %s);
                """

            self.db.insert(query, card)

    def empty_db(self):
        """ Calls for truncate of all tables used by Connector. """

        self.db.insert("SET FOREIGN_KEY_CHECKS=0")
        self.db.truncate_table('sdk_editions')
        self.db.truncate_table('sdk_cards')
        self.db.insert("SET FOREIGN_KEY_CHECKS=1")
