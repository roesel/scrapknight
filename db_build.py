#!/usr/bin/env python
# -*- coding: utf-8 -*-

from libs.builder import Builder
from config_db import config


bu = Builder(config)
bu.load_sql('install/empty_db.sql')
bu.load_sql('install/init_db.sql')
bu.load_sql('install/rel_editions.sql')
