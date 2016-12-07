#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This script creates a new Scraper object and builds the database according to the methods called.
The object is then thrown away, so any results must be stored elsewhere to persist.
This only gets data from CR eshop and nothing else.
"""

from libs.connector import Connector
from config_db import config


sdk = Connector(config)
# sdk.load_editions()
sdk.load_list_of_editions(['KLD', 'SOI', 'BFZ'])
