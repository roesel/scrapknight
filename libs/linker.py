#!/usr/bin/env python
# -*- coding: utf-8 -

import time
from datetime import datetime

from libs.database import Database
from libs.matcher import Matcher
from libs.connector import Connector
from libs.scraper import Scraper

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
        self.sc = Scraper(self.db)
        self.co = Connector(self.db)

    def link(self, eds):
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
        TODO: all-editions should use the relation table and allow passing 2 different editions to link_edition(s)
        """
        if eds == []:
            editions = []
            editions_sc = self.sc.get_edition_list()
            editions_co = self.co.get_edition_list()

            ed_sc = []
            for ed in editions_sc:
                ed_sc.append(ed[0])

            ed_co = []
            for ed in editions_co:
                ed_co.append(ed[0])

            for edition in ed_sc:
                if edition in ed_co:
                    editions.append(edition)
        else:
            editions = eds

        for edition in editions:
            self.link_edition(edition)

    def link_edition(self, edition):
        api_original = self.total("api", edition)
        api_standard = self.standard("api", edition)
        cr_original = self.total("cr", edition)
        cr_standard = self.standard("cr", edition)

        n_directly_matching = self.direct_matches(edition)
        if cr_standard >= api_standard:
            n_cards = cr_standard
        else:
            n_cards = api_standard
        n_missing_cards = n_cards - n_directly_matching
        n_inserted = 0

        self.trouble = []

        # Is it reasonable to try direct matching?
        if n_directly_matching > 0:
            n_direct_inserted = self.insert_direct_match(edition)
            n_inserted += n_direct_inserted
            if n_direct_inserted != n_directly_matching:
                self.trouble.append("{}/{} direct inserted".format(
                    n_direct_inserted, n_directly_matching))

        # Is it reasonable to try image matching?
        if api_standard == cr_standard:
            # Is there even anything to image match?
            if n_missing_cards > 0:
                n_image_matched = self.image_match(edition)
                n_inserted += n_image_matched
                if n_image_matched != n_missing_cards:
                    self.trouble.append("{}/{} image_matches inserted".format(
                        n_image_matched, n_missing_cards))
        else:
            self.trouble.append("API ({} -> {}) / CR ({} -> {}) mismatch".format(
                api_original, api_standard, cr_original, cr_standard))

        # Final report
        if len(self.trouble):
            trouble_string = "(" + ", ".join(self.trouble) + ")"
        else:
            trouble_string = ""

        if n_inserted == n_cards:
            log.info("{}: {}% ({}/{} cards inserted) {}".format(
                edition, int(100 * n_inserted / n_cards), n_inserted, n_cards, trouble_string))
        else:
            log.info("{}: {}% ({}/{} cards inserted) {}".format(
                edition, int(100 * n_inserted / n_cards), n_inserted, n_cards, trouble_string))

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
            matches, info = m.get_matches()
            if matches is not None:
                log.debug("All matches are unambiguous (unique).")
                self.insert_image_match(matches)
                return len(matches)
            else:
                self.trouble.append("matcher: {}.".format(info))
                return 0
        else:
            log.debug("{}: WARNING: image_match() found {} in API and {} in CR. Not even trying.".format(
                edition, len(api_ids), len(cr_ids)))
            self.trouble.append("image_match uneven {}!={}".format(len(api_ids), len(cr_ids)))
            return 0

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
        if number_of_changed_rows % 2 == 0:
            return int(number_of_changed_rows / 2)
        else:
            return number_of_changed_rows / 2
