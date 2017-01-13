#!/usr/bin/env python
# -*- coding: utf-8 -

import time
from datetime import datetime

from libs.database import Database
from libs.matcher import Matcher

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

    def link(self, editions):
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
        for edition in editions:
            self.link_edition(edition)

    def link_edition(self, edition):
        api_original = self.total("api", edition)
        api_standard = self.standard("api", edition)
        cr_original = self.total("cr", edition)
        cr_standard = self.standard("cr", edition)

        output_line = str(edition) + ": "
        matching_sources = False
        if api_standard != cr_standard:
            log.info(output_line)
            log.info("    API and CR both have different # of cards. Direct match only.")
            log.info("    API: {} -> {}.".format(api_original, api_standard))
            log.info("    CR: {} -> {}.".format(cr_original, cr_standard))
        else:
            matching_sources = True

        n_cards = api_standard
        n_directly_matching = self.direct_matches(edition)
        n_missing_cards = n_cards - n_directly_matching
        output_line += "{}/{} matching".format(n_directly_matching, n_cards)

        # TODO check how many rows were inserted and confirm w/ direct_matches()
        changed_rows = self.insert_direct_match(edition)
        if changed_rows != n_directly_matching:
            log.info(output_line)
            log.info(
                "WARNING: Not all directly matching cards inserted ({}/{}).".format(changed_rows, n_directly_matching))

        if not matching_sources:
            output_line += " - PROBLEMS"
            log.info(output_line)
        else:
            if n_missing_cards > 0:
                n_image_matched = self.image_match(edition)
                output_line += ", {}/{} image_matched".format(n_image_matched, n_missing_cards)
                if n_image_matched != n_missing_cards:
                    log.info(output_line)
                    log.info("WARNING: not all missing fixed by image_match().")
                else:
                    output_line += " - OK"

            else:
                output_line += " - OK (probably black magic)"
            log.info(output_line)

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

    def image_match(self, edition):
        """
        Tries to match cards not covered by direct_matches() using differences in images.

        IMPROVE Could be optimized to make a new matcher for every kind of land in order
        to only do 3x3 matrices for 'Plains' instead of 15x15 for all lands.
        """
        cr_ids = self.extra_from_cr(edition)
        api_ids = self.extra_from_api(edition)

        if len(cr_ids) == len(api_ids):
            m = Matcher(cr_ids, api_ids)
            matches, status = m.get_matches()
            if status:
                log.debug("All matches are unambiguous (unique).")
            self.insert_image_match(matches)

            # TODO: this is a cheat, we need to actually check rows in DB!
            return len(matches)
        else:
            log.info("WARNING: Image match would get uneven arrays -> not matching.")

    def insert_image_match(self, matches):
        """
        Replaces new values into `rel_cards`.
        TODO: find out the amount inserted to report back
        """
        log.debug("Inserting image match...")
        for cr_id, mid in matches.items():
            query = """
                REPLACE INTO `rel_cards`
                    (`id_cr`, `id_sdk`)
                VALUES
                    (%s, %s);
                """

            self.db.insert(query, [cr_id, mid])
        log.debug("Done.")

    def extra_from_cr(self, edition):
        """
        Returns a list of cards from CR that are not covered by direct_matches().
        """
        query_cr = """
                SET @edition = "{}";

            	SELECT id_cr
            	FROM (
            		SELECT * FROM sdk_cards WHERE NOT (`layout`="double-faced" and mana_cost is null and `type` !="Land") AND (`set`=@edition)
            	) as t1
            	RIGHT JOIN (
            		SELECT REPLACE(name,'´', '\\\'') as name_replaced, id as id_cr FROM cards WHERE edition_id=@edition AND id not like "tokens%" AND name not like "Token - %" AND name not like "Emblem - %"
            	) as t2
            	ON t1.name = t2.name_replaced
            	WHERE `name` is null;
                """.format(edition)

        results = self.db.cursor.execute(query_cr, multi=True)
        self.db.cnx.commit()
        out = []
        for cur in results:
            if cur.with_rows:
                rows = cur.fetchall()
                for row in rows:
                    out.append(row[0])
        return out

    def extra_from_api(self, edition):
        """
        Returns a list of cards from API that are not covered by direct_matches().
        """
        query_cr = """
                SET @edition = "{}";

                SELECT mid
            	FROM (
            		SELECT * FROM sdk_cards WHERE NOT (`layout`="double-faced" and mana_cost is null and `type` !="Land") AND (`set`=@edition)
            	) as t1
            	LEFT JOIN (
            		SELECT REPLACE(name,'´', '\\\'') as name_replaced FROM cards WHERE edition_id=@edition AND id not like "tokens%" AND name not like "Token - %" AND name not like "Emblem - %"
            	) as t2
            	ON t1.name = t2.name_replaced
            	WHERE `name_replaced` is null;
                """.format(edition)

        results = self.db.cursor.execute(query_cr, multi=True)
        self.db.cnx.commit()
        out = []
        for cur in results:
            if cur.with_rows:
                rows = cur.fetchall()
                for row in rows:
                    out.append(row[0])
        return out

    def insert_direct_match(self, edition):
        query = """ SET @edition = %s ;
                    REPLACE INTO rel_cards
                    SELECT `id_cr`, `mid` as `id_sdk` FROM (
                       SELECT REPLACE(name,'´', '\\\'') as name_replaced, `id` as `id_cr` from cards where edition_id = @edition
                       ) as cr
                    JOIN (
                       SELECT * from sdk_cards where `set` = @edition
                       ) as api
                    ON cr.name_replaced = api.name;
        """
        number_of_changed_rows = self.db.multiinsert(query, (edition,))
        return number_of_changed_rows / 2
