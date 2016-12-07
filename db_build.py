#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import getopt

from libs.builder import Builder
from config_db import config

import logging
import pprint

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
            print("No help so far, sorry!")
            sys.exit()
        else:
            assert False, "unhandled option"

    # Set logging level
    logging.basicConfig(
        format='%(levelname)s:%(message)s',
        level=logging_level)

def build():
    """
    """

    log = logging.getLogger()

    bu = Builder(config)

    log.info("Deleting database")
    bu.load_sql('install/empty_db.sql')

    log.info("Initializing database")
    bu.load_sql('install/init_db.sql')

    log.info("Linking editions")
    bu.load_sql('install/rel_editions.sql')


if __name__ == "__main__":
    setup()
    build()
