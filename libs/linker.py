#!/usr/bin/env python
# -*- coding: utf-8 -

import time
from datetime import datetime

from libs.database import Database

import logging
import pprint

log = logging.getLogger()


class Linker:
    """
    Dedicated to linking SDK and CR. Works with the DB directly, after building.
    """
    # self.db = Database()

    def __init__(self, db_config):
        """
        Creates a Database() object and passes it to Scraper/Connector upon creation.
        """
        self.db = Database(db_config)

    def link(self):
        """
        For each edition:
          1) relate through rel_editions to get "edition_sdk" and "edition_cr"
          2) count how many cards total
          3) count how many special cards (tokens, emblems)
          4) count how many cards match directly (and how many missing)
          5) count how many mismatching cards
            5a) has to be an even number
            5b) has to add up to total - special
          6) ...magic...
          7) ...
          8) profit
        """
        pass

    def total(self, source, edition):
        count = -1
        if source == "api":
            query = """SELECT COUNT(*) FROM `sdk_cards` WHERE `set` = "{}";""".format(edition)
            result = self.db.query(query)
            count = result[0][0]
        elif source == "cr":
            query = """SELECT COUNT(*) FROM `cards` WHERE `edition_id` = "{}";""".format(edition)
            result = self.db.query(query)
            count = result[0][0]
        return count

    def standard(self, source, edition):
        count = -1
        if source == "api":
            pass
            # Korekce na druhé strany double-faced karet (SOI, ...)
            query = """SELECT COUNT(*) FROM sdk_cards WHERE NOT (`layout`="double-faced" and mana_cost is null and `type` !="Land") AND (`set`="{}");""".format(edition)
            result = self.db.query(query)
            count = result[0][0]
        elif source == "cr":
            query = """SELECT COUNT(*) FROM `cards` WHERE `edition_id` = "{}" AND id not like "tokens%" AND name not like "Token - %" AND name not like "Emblem - %";""".format(edition)
            result = self.db.query(query)
            count = result[0][0]
        return count

    def direct_matches(self, edition):
        query = """ SET @edition = "{}";
                    SELECT COUNT(*) FROM (
                        SELECT REPLACE(name,'´', '\\\'') as name_replaced from cards where edition_id = @edition
                        ) as cr
                    JOIN (
                        SELECT * from sdk_cards where `set` = @edition
                        ) as api
                    ON cr.name_replaced = api.name;
                """.format(edition)
        results = self.db.cursor.execute(query, multi=True)
        self.db.cnx.commit()
        for cur in results:
            if cur.with_rows:
                count = cur.fetchall()[0][0]

        return count

    def landsort(self, edition):
        query = """
                SET @edition = "{}";
                SELECT COUNT(*) FROM (
                	(SELECT *
                	FROM (
                		SELECT * FROM sdk_cards WHERE NOT (`layout`="double-faced" and mana_cost is null and `type` !="Land") AND (`set`=@edition)
                	) as t1
                	RIGHT JOIN (
                		SELECT REPLACE(name,'´', '\\\'') as name_replaced FROM cards WHERE edition_id=@edition AND id not like "tokens%" AND name not like "Token - %" AND name not like "Emblem - %"
                	) as t2
                	ON t1.name = t2.name_replaced)

                UNION ALL

                	(SELECT *
                	FROM (
                		SELECT * FROM sdk_cards WHERE NOT (`layout`="double-faced" and mana_cost is null and `type` !="Land") AND (`set`=@edition)
                	) as t1
                	LEFT JOIN (
                		SELECT REPLACE(name,'´', '\\\'') as name_replaced FROM cards WHERE edition_id=@edition AND id not like "tokens%" AND name not like "Token - %" AND name not like "Emblem - %"
                	) as t2
                	ON t1.name = t2.name_replaced)
                ) as mismatch WHERE (`name` is  null or `name_replaced` is  null);
                """.format(edition)

        results = self.db.cursor.execute(query, multi=True)
        self.db.cnx.commit()
        for cur in results:
            if cur.with_rows:
                count = cur.fetchall()[0][0]

        return count / 2

    def insert_landsort(self, edition):
        query = """ SET @edition = %s;
                    REPLACE INTO rel_cards
                    SELECT `id_cr`, `mid` as `id_sdk`
                    FROM (
                    select @r := @r+1 as my_order , z.* from(

                    SELECT *
                       FROM (
                               SELECT * FROM sdk_cards WHERE NOT (`layout`="double-faced" and mana_cost is null and `type` !="Land") AND (`set`=@edition)
                       ) as t1
                       LEFT JOIN (
                               SELECT REPLACE(name,'´', '\\\'') as name_replaced FROM cards WHERE edition_id=@edition AND id not like "tokens%" AND name not like "Token - %"
                       ) as t2
                       ON t1.name = t2.name_replaced
                       WHERE `name_replaced` is null
                       ORDER BY `name`, `mid`

                    )z, (select @r:=0)y
                    ) as not_in_cr

                    JOIN

                    (
                    select @s := @s+1 as my_order , z.* from(

                    SELECT *
                       FROM (
                               SELECT `name` FROM sdk_cards WHERE NOT (`layout`="double-faced" and mana_cost is null and `type` !="Land") AND (`set`=@edition)
                       ) as t1
                       RIGHT JOIN (
                               SELECT REPLACE(name,'´', '\\\'') as name_cr, id as id_cr FROM cards WHERE edition_id=@edition AND id not like "tokens%" AND name not like "Token - %"
                       ) as t2
                       ON t1.name = t2.name_cr
                       WHERE `name` is null
                       ORDER BY `name_cr`

                    )z, (select @s:=0)y
                    ) as not_in_api
                           ON not_in_cr.my_order = not_in_api.my_order;
        """
        results = self.db.multiinsert(query, (edition,))

    def insert_direct_match(self, edition):
        query = """ SET @edition = %s;
                    REPLACE INTO rel_cards
                    SELECT `id_cr`, `mid` as `id_sdk` FROM (
                       SELECT REPLACE(name,'´', '\\\'') as name_replaced, `id` as `id_cr` from cards where edition_id = @edition
                       ) as cr
                    JOIN (
                       SELECT * from sdk_cards where `set` = @edition
                       ) as api
                    ON cr.name_replaced = api.name;
        """
        results = self.db.multiinsert(query, (edition,))
