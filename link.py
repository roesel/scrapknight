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


def link(editions):
    """
    Tries to link card entries from API with entries from CR.
    """

    log = logging.getLogger()

    l = Linker(DatabaseConfig)

    l.link(editions)


if __name__ == "__main__":
    setup()

    #editions = []
    editions = ['AER', 'KLD', 'KLI', 'EMN', 'SOI', 'OGW', 'BFZ']
    #editions = ['M15', 'M14', 'M13', 'M12', 'M11', 'M10', '10E', '9ED', '8ED']
    #editions = ['M14', '9ED']

    link(editions)
