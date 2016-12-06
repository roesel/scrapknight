#!/usr/bin/env python
# -*- coding: utf-8 -

from database import Database
from mtgsdk import Set
from mtgsdk import Card
import time


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
        Truncates `sdk_editions` table, then inserts pairs of (edition_id, edition_name into DB).
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

    def load_cards(self, edition):
        """
        Loads all editions from the API.
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

        if self.debug:
            print("Found {} cards in API. Starting to fetch.".format(number_of_cards))

        cards = []
        for c in all_cards:
            cards.append([c.name, c.multiverse_id, c.layout,
                          c.mana_cost, c.type, c.rarity, c.set, c.id])

        if self.debug:
            print("Inserting {} cards into DB.".format(len(cards)))

        self.insert_cards(cards)

    def insert_cards(self, cards):
        """
        Inserts new values into sdk_cards.
        """
        for card in cards:
            query = """
                INSERT INTO `sdk_cards`
                    (`name`, `mid`, `layout`, `mana_cost`, `type`, `rarity`, `set`, `id`)
                VALUES
                    (%s, %s, %s, %s, %s, %s, %s, %s);
                """

            self.db.insert(query, card)

    def load_list_of_editions(self, list_of_editions):
        self.db.truncate_table('sdk_cards')

        for e in list_of_editions:
            print("Sleeping for 5 seconds...")
            time.sleep(5)
            print("Loading edition {} from API...".format(e))
            self.load_cards(e)


sdk = Connector()
# sdk.load_editions()
sdk.load_list_of_editions(['KLD', 'SOI', 'BFZ'])
