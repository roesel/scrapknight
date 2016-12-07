#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This script creates a new Scraper object and builds the database according to the methods called.
The object is then thrown away, so any results must be stored elsewhere to persist.
This only gets data from CR eshop and nothing else.
"""

from libs.scraper import Scraper
from config_db import config

sc = Scraper(config)
sc.rebuild_db()
for i in sc.get_db_info():
    print(i)
