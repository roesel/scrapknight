#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import getopt

from libs.builder import Builder
from app.config import DatabaseConfig

import logging
import pprint

HELP = '''
DESCRIPTION
Builds the database according to functions specified in build(). It should be able to (IN THEORY) run either
    a) with enough privileges to create database and then drop and create everything from scratch, or
    b) on a database called `scrapknight` already created and with sufficient privileges to drop tables/views and create after.
Only a) is implemented as of now.

The idea is that Builder is the only object you need to call and it calls Scraper/Connector itself down the line. But this might change.
If this wasn't enough ingormation, please feel free to #helpyourself.

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


def build():
    """
    (Re)builds the database completely from scratch, to the state we consider the "default".
    What "default" is can change drastically between commits though.
    """

    log = logging.getLogger()

    DatabaseConfig['raise_on_warnings'] = False

    bu = Builder(DatabaseConfig)

    log.info("Loading SQL files:")
    log.info("  - Deleting database")
    bu.load_sql('install/empty_db.sql')

    log.info("  - Initializing database")
    bu.load_sql('install/init_db.sql')

    log.info("  - Linking editions")
    bu.load_sql('install/rel_editions.sql')

    log.info("  - Linking cards (!)")
    bu.load_sql('install/rel_cards.sql')

    log.info("Filling up database:")

    editions = ['KLD', 'EMN', 'SOI', 'OGW', 'BFZ']
    bu.build(editions)


if __name__ == "__main__":
    setup()
    build()
