import datetime

from flask_login import UserMixin

"""App Configuration"""

from .config import DatabaseConfig

""" DB Models """

from libs.database import Database
from .deck import Deck

from .shared_stuff import db


class User(db.Model, UserMixin):

    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=True)
    avatar = db.Column(db.String(200))
    tokens = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow())

    def owns_card(self, card):

        query = """
            SELECT `count`
            FROM `users_cards`
            WHERE `user_id` = %s AND `card_id` = %s
            """

        result = self.db.query(query, (self.id, card.id))

        if result:
            return result[0][0]
        else:
            return False

    def save_library(self, deck):

        query = """
            DELETE FROM `users_cards`
            WHERE
            `user_id` = %s
            """

        self.db.insert(
            query, (self.id,))

        return self.save_cards(deck)

    def save_cards(self, deck):

        for card in deck.cards:
            if card.found:
                query = """
                    INSERT INTO `users_cards`
                    (`user_id`, `card_id`, `count`)
                    VALUES
                    (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE count=count+%s
                    """

                self.db.insert(
                    query, (self.id, card.id, card.count, card.count))

        return True

    def save_deck(self, deck_id, deck):

        query = """
            SELECT *
            FROM `users_decks`
            WHERE `id` = %s AND `user_id` = %s
            """

        result = self.db.query(query, (deck_id, self.id,))

        if not result:
            # Create the deck first
            query = """
                INSERT INTO `users_decks`
                (`user_id`)
                VALUES
                (%s)
                """
            print(query)

            deck_id = self.db.insert(
                query, (self.id,))

        query = """
            DELETE FROM `users_decks_cards`
            WHERE
            `deck_id` = %s AND `user_id` = %s
            """

        self.db.insert(
            query, (deck_id, self.id,))

        for card in deck.cards:
            print(card.found)
            if card.found:
                query = """
                    INSERT INTO `users_decks_cards`
                    (`deck_id`, `user_id`, `card_id`, `count`)
                    VALUES
                    (%s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE count=count+%s
                    """

                self.db.insert(
                    query, (deck_id, self.id, card.id, card.count, card.count,))

        return deck_id

    def get_library(self):

        query = """
            SELECT `card_id`, `count`
            FROM `users_cards`
            WHERE `user_id` = %s
            """

        cards = self.db.query(query, (self.id,))
        library = [{'id': c[0], 'count': c[1]} for c in cards]

        return Deck(card_list=library)

    def get_deck(self, deck_id):

        query = """
            SELECT `c`.`card_id`, `c`.`count`
            FROM `users_decks` AS `d`
            INNER JOIN `users_decks_cards` AS `c`
            ON `d`.`id` = `c`.`deck_id` AND `d`.`user_id` = `c`.`user_id`
            WHERE `d`.`user_id` = %s AND `d`.`id` = %s
            """

        cards = self.db.query(query, (self.id, deck_id,))
        cards = [{'id': c[0], 'count': c[1]} for c in cards]

        return Deck(card_list=cards)

    def get_deck_list(self):

        query = """
            SELECT `d`.`id`, `d`.`name`, `d`.`info`, SUM(`c`.`count`)
            FROM `users_decks` AS `d`
            LEFT JOIN `users_decks_cards` AS `c`
            ON `d`.`id` = `c`.`deck_id` AND `d`.`user_id` = `c`.`user_id`
            WHERE `d`.`user_id` = %s
            GROUP BY `d`.`id`, `d`.`user_id`
            ORDER BY `d`.`id` ASC
            """

        decks = self.db.query(query, (self.id,))

        # If user has no decks yet, the query returns [(None, None, ..., None,)]
        if len(decks) == 1 and not any(decks[0]):
            decks = []

        decks = [{
            'id': d[0],
            'name': d[1],
            'info': d[2],
            'card_count': d[3]} for d in decks]

        return decks


User.db = Database(DatabaseConfig)
