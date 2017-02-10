import numpy as np

from libs.database import Database
from app.config import DatabaseConfig

outlog = []

import logging

from .deck import Deck
from .card import Card
from .multicard import Multicard

logging_level = logging.INFO
# logging_level = logging.DEBUG

# Set logging level
logging.basicConfig(
    format='%(levelname)s: %(message)s',
    level=logging_level)

log = logging.getLogger()


def process(user, user_input):

    outlog = []

    Card.db = Database(DatabaseConfig)

    mydeck = Deck(user=user, user_input=user_input)

    return mydeck.print_price_table()


def process_by_id(card_id):

    outlog = []

    Card.db = Database(DatabaseConfig)

    card_list = [{'id': card_id, 'count': 1},]

    mydeck = Deck(card_list=card_list)

    price_table, l = mydeck.print_price_table()

    card_details = price_table['body'][0]

    return card_details, price_table, l


def print_user_deck(user, deck_id):

    outlog = []

    Card.db = Database(DatabaseConfig)

    mydeck = user.get_deck(deck_id)

    return mydeck.print_price_table()


def print_user_library(user):

    outlog = []

    Card.db = Database(DatabaseConfig)

    mydeck = user.get_library()

    return mydeck.print_price_table()


def users_cards_save(user, user_input):

    outlog = []

    Card.db = Database(DatabaseConfig)

    mydeck = Deck(user_input=user_input)

    user.save_cards(mydeck)


def save_user_library(user, user_input):

    outlog = []

    Card.db = Database(DatabaseConfig)

    mydeck = Deck(user_input=user_input)

    return user.save_library(mydeck)


def modify_user_deck(user, deck_id, user_input):

    outlog = []

    Card.db = Database(DatabaseConfig)

    mydeck = Deck(user_input=user_input)

    return user.save_deck(deck_id, mydeck)


def levenshtein(source, target):
    """
    Source: https://en.wikibooks.org/wiki/Algorithm_Implementation/Strings/Levenshtein_distance#Python
    """
    if len(source) < len(target):
        return levenshtein(target, source)

    # So now we have len(source) >= len(target).
    if len(target) == 0:
        return len(source)

    # We call tuple() to force strings to be used as sequences
    # ('c', 'a', 't', 's') - numpy uses them as values by default.
    source = np.array(tuple(source))
    target = np.array(tuple(target))

    # We use a dynamic programming algorithm, but with the
    # added optimization that we only need the last two rows
    # of the matrix.
    previous_row = np.arange(target.size + 1)
    for s in source:
        # Insertion (target grows longer than source):
        current_row = previous_row + 1

        # Substitution or matching:
        # Target and source items are aligned, and either
        # are different (cost of 1), or are the same (cost of 0).
        current_row[1:] = np.minimum(
            current_row[1:],
            np.add(previous_row[:-1], target != s))

        # Deletion (target grows shorter than source):
        current_row[1:] = np.minimum(
            current_row[1:],
            current_row[0:-1] + 1)

        previous_row = current_row

    return previous_row[-1]
