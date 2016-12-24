#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import getopt

from libs.linker import Linker
from config_db import config

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

    l = Linker(config)
    
    edition = "SOI"
    
    print("API total(): {}".format(l.total("api", edition)))
    print("API standard(): {}".format(l.standard("api", edition)))
    
    print("CR total(): {}".format(l.total("cr", edition)))
    print("CR standard(): {}".format(l.standard("cr", edition)))
    
    print("Direct matches: {}".format(l.direct_matches(edition)))
    
    print("We are missing {} cards.".format(l.standard("api", edition) - l.direct_matches(edition)))
    print("Landsort offers {} cards.".format(l.landsort(edition)))
    


if __name__ == "__main__":
    setup()
    link()
