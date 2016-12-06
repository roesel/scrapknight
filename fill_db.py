#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This script creates a new Scraper object and rebuilds the database according to the methods called.
The object is then thrown away, so any results must be stored elsewhere to persist.
"""

from scraper import Scraper

sc = Scraper()
sc.rebuild_db()
for i in sc.get_db_info():
    print(i)
