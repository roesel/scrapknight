#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import getopt

from libs.connector import Connector
from config_db import config

import logging
import pprint

HELP = """
No help so far, sorry!
"""

def setup():
    """
    """

    # Parse commanda line parameters
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

def connect():
    """
    """

    log = logging.getLogger()

    sdk = Connector(config)
    # sdk.load_editions()

    log.info("Loading list of editions.")
    sdk.load_list_of_editions(['KLD', 'SOI', 'BFZ'])


if __name__ == "__main__":
    setup()
    connect()
