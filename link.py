#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import getopt

from libs.linker import Linker
from app.config import DatabaseConfig

import logging
import pprint

HELP = '''
DESCRIPTION

WANTED dead or alive

OPTIONS
-v (--verbose)
    Raises logging level to DEBUG, prints anything in log.debug()
-h (--help)
    Show a summary of command line options and exit.
'''


def setup():
    """
    Sets up arg parsing and logging options. Bubbles down to other generated objects.
    """

    # Parse command line parameters
    try:
        opts, args = getopt.getopt(sys.argv[1:], "ho:v", ["help"])
    except getopt.GetoptError as err:
        # print help information and exit:
        print(str(err))  # will print something like "option -a not recognized"
        usage()
        sys.exit(2)

    logging_level = logging.INFO

    for o, a in opts:
        if o in ("-v", "--verbose"):
            logging_level = logging.DEBUG
        elif o in ("-h", "--help"):
            print(HELP)
            sys.exit()
        else:
            assert False, "unhandled option"

    # Set logging level
    logging.basicConfig(
        format='%(levelname)s: %(message)s',
        level=logging_level)


def link():
    """
    (Re)builds the database completely from scratch, to the state we consider the "default".
    What "default" is can change drastically between commits though.
    """

    log = logging.getLogger()

    l = Linker(DatabaseConfig)

    edition = "SOI"

    api_original = l.total("api", edition)
    api_standard = l.standard("api", edition)
    cr_original = l.total("cr", edition)
    cr_standard = l.standard("cr", edition)

    log.info("API: {} -> {}.".format(api_original, api_standard))
    log.info(" CR: {} -> {}.".format(cr_original, cr_standard))
    if api_standard == cr_standard:
        n_cards = api_standard
        n_directly_matching = l.direct_matches(edition)
        n_missing_cards = n_cards - n_directly_matching
        log.info("API and CR # of cards matching, good.")

        log.info("{} directly matching cards.".format(n_directly_matching))
        log.info("Inserting direct matches...")
        # check how many rows were inserted and confirm w/ direct_matches()
        l.insert_direct_match(edition)

        if n_missing_cards > 0:
            log.info("{} cards are mismatching.".format(n_missing_cards))
            log.info("Trying image match.")
            l.image_match(edition)
        else:
            log.info("All cards matched directly. Yay!")
    else:
        log.info("API and CR both have different # of cards. Cancelling.")


if __name__ == "__main__":
    setup()
    link()
