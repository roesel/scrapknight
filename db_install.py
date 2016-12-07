#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import getopt

import db_build
import db_connect
import db_scrape

import logging
import pprint

HELP = """
No help so far, sorry!
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

if __name__ == "__main__":
    setup()
    db_build.build()
    db_connect.connect()
    db_scrape.scrape()
