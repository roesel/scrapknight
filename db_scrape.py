#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import getopt

from libs.scraper import Scraper
from config_db import config

import logging
import pprint

HELP = """
This script creates a new Scraper object and builds the database according to the methods called.
The object is then thrown away, so any results must be stored elsewhere to persist.
This only gets data from CR eshop and nothing else.
"""

def setup():
    """
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
        format='%(levelname)s:%(message)s',
        level=logging_level)

def scrape():
    """
    """

    log = logging.getLogger()

    sc = Scraper(config)
    sc.rebuild_db()
    for i in sc.get_db_info():
        print(i)

if __name__ == "__main__":
    setup()
    scrape()
