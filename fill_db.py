#!/usr/bin/env python
# -*- coding: utf-8 -*-
from scraper import Scraper

sc = Scraper()
sc.rebuild_db()
for i in sc.get_db_info():
    print(i)
