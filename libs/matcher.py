#!/usr/bin/env python
# -*- coding: utf-8 -

from PIL import Image
import imagehash
import urllib
from io import BytesIO
import numpy as np
import time
from pathlib import Path

import logging
logging.getLogger("requests").setLevel(logging.WARNING)
log = logging.getLogger()


class Matcher:
    """
    Tries to match cards by image. #greatidea #notwaistingtimeatall
    """
    # self.list_cr
    # self.list_mid

    def __init__(self, list_cr, list_mid):
        """
        Runs matching on received lists.
        """
        self.list_cr = list_cr
        self.list_mid = list_mid
        self.info_status = []

    def get_matches(self):
        start = time.time()
        results = self.match(self.list_cr, self.list_mid)
        match_took = time.time() - start

        log.debug("Matching took {}.".format(self.readable_time(match_took)))

        if len(self.info_status):
            out_info = "(" + ",".join(self.info_status) + ")"
        else:
            out_info = None

        return results, out_info

    def readable_time(self, seconds):
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        return "%d:%02d:%02d" % (h, m, s)

    def matrix(self, list_cr, list_mid):
        """
        Creates a nxn matrix with distances of all images to each other.
        """
        imgs_cr = [self.get_img("cr", id_cr) for id_cr in list_cr]
        imgs_api = [self.get_img("api", mid) for mid in list_mid]

        if (None not in imgs_cr) and (None not in imgs_api):
            mat = np.zeros([len(imgs_cr), len(imgs_api)])
            for i in range(len(imgs_cr)):
                for j in range(len(imgs_api)):
                    mat[i][j] = self.dist(imgs_cr[i], imgs_api[j])
        else:
            self.info_status.append("wrong url(s)")
            mat = None

        return mat

    def match(self, list_cr, list_mid):
        """
        Generates dictionary of cr_ids matching mids.
        """
        mat = self.matrix(list_cr, list_mid)
        if mat is not None:
            minima_locations = self.get_minima(mat)
            if minima_locations is not None:
                out = {}
                for i in range(len(minima_locations)):
                    if minima_locations[i] != -1:
                        out[list_cr[i]] = list_mid[minima_locations[i]]

                return out
            else:
                return None
        else:
            return None

    def get_min_info(self, m, a):
        if a == 1:
            m = m.T
        min_loc = np.argmin(m.T, axis=0)
        min_val = np.amin(m.T, axis=0)
        occ = np.zeros_like(min_loc)
        duplicates = [None for i in range(len(occ))]
        for i in range(len(min_loc)):
            dupl = np.where(m[i] == min_val[i])[0]
            occ[i] = len(dupl) - 1
            if len(dupl) > 1:
                duplicates[i] = dupl

        return min_loc, min_val, occ, duplicates

    def get_minima(self, m):
        acceptable_minimum = 16
        xmin_loc, xmin_val, xocc, xdupl = self.get_min_info(m, 0)
        ymin_loc, ymin_val, yocc, ydupl = self.get_min_info(m, 1)
        # print(m)

        xout = np.negative(np.ones_like(xmin_loc))
        yout = np.negative(np.ones_like(ymin_loc))

        max_dif = 0

        # scroll by x and see perfect matches
        x_inserted = 0
        for i in range(len(xocc)):
            if xmin_val[i] <= acceptable_minimum:
                if xocc[i] <= 0:  # if no duplicates
                    if ymin_loc[xmin_loc[i]] == i:
                        xout[i] = xmin_loc[i]
                        yout[xmin_loc[i]] = ymin_loc[xmin_loc[i]]
                        x_inserted += 1
                    else:
                        log.debug('x minimum found, but not minimum for y, {} -> {} (i={}, xocc={}).'.format(
                            self.list_cr[xmin_loc[i]], self.list_mid[i], i, xocc[i]))
            elif xmin_val[i] > max_dif:
                max_dif = xmin_val[i]

        #print('x - duplicates ({} inserted)'.format(x_inserted))
        for k in range(len(xdupl)):
            if xdupl[k] is not None:
                for candidate in xdupl[k]:
                    log.debug("Ambiguous candidate: {} -> {}".format(self.list_cr[k], self.list_mid[candidate]))

        # scroll by y and for unmatched see perfect matches
        y_inserted = 0
        for j in range(len(yocc)):
            if yout[j] == -1:
                if ymin_val[j] <= acceptable_minimum:
                    if yocc[j] == 0:  # if no duplicates
                        if xmin_loc[ymin_loc[j]] == j:
                            yout[j] = ymin_loc[j]
                            xout[ymin_loc[j]] = xmin_loc[ymin_loc[j]]
                            y_inserted += 1
                        else:
                            log.debug('y minimum found, but not minimum for x, {} -> {} (j={}).'.format(
                                self.list_mid[ymin_loc[j]], self.list_cr[j], j))
                elif ymin_val[j] > max_dif:
                    max_dif = ymin_val[j]

        #print('y - duplicates ({} inserted)'.format(y_inserted))
        for k in range(len(ydupl)):
            if ydupl[k] is not None:
                for candidate in ydupl[k]:
                    log.debug("Ambiguous candidate: {} -> {}".format(self.list_mid[k], self.list_cr[candidate]))

        if max_dif > acceptable_minimum:
            self.info_status.append("max dif {} >= {}".format(max_dif, acceptable_minimum))

        return xout

    def get_minima_2(self, mat):
        minima = []
        minima_locations = []

        dim = len(mat[0])
        occurences = [0] * dim
        unambiguous = True
        for i in range(dim):
            minimum_location = np.argmin(mat.T[i])
            minimum = mat.T[i][minimum_location]
            all_minima = np.where(mat.T[i] == minimum)
            if len(all_minima[0]) != 1:
                unambiguous = False
                occurences[i] = all_minima[0]

            minima.append(minimum)
            minima_locations.append(minimum_location)

        acceptable_minimum = 11

        if unambiguous:
            status = 1
        else:
            status = 0
            self.info_status.append("ambiguous")
            log.debug("Some matches are ambiguous.")
            for i in range(len(occurences)):
                try:
                    for candidate in occurences[i]:
                        # TODO Not sure which index is which - might be switched CR/API
                        log.debug(
                            "Ambiguous candidate: {} -> {}".format(self.list_cr[i], self.list_mid[candidate]))
                except:
                    pass

        max_difference = np.max(minima)
        if max_difference < acceptable_minimum:
            log.debug("Maximum difference in images was {}.".format(max_difference))
        else:
            status = 0
            self.info_status.append("max dif {} >= {}".format(max_difference, acceptable_minimum))
            log.debug("WARNING! Maximum difference {} >= {}. Trouble?".format(max_difference, acceptable_minimum))

        if status:
            return minima_locations
        else:
            return None

    def dist(self, image_1, image_2):
        """
        Calculates distance of two images.
        """
        hash_1 = imagehash.average_hash(image_1)

        hash_2 = imagehash.average_hash(image_2)

        return hash_1 - hash_2

    def get_img(self, type_id, card_id):
        if type_id == "cr":
            url = self.url_cr(card_id)
            name = str(card_id) + ".jpg"
        else:
            url = self.url_api(card_id)
            name = str(card_id) + ".png"

        directory = Path('app/static/img/cards/')
        directory.mkdir(exist_ok=True)
        path = directory / name

        if path.exists():
            img = Image.open(path)
            return img
        else:
            try:
                urllib.request.urlretrieve(url, str(path))
                img = Image.open(path)
                return img
            except urllib.error.URLError as e:
                log.debug("URLError, trouble...")
                return None

    def url_cr(self, id_cr):
        """
        Generates cr_url from id_cr.
        """
        return 'http://cernyrytir.cz/images/kusovkymagic/' + id_cr.replace('_', '/') + '.jpg'

    def url_api(self, mid):
        """
        Generates api_url from mid.
        """
        return 'https://image.deckbrew.com/mtg/multiverseid/' + str(mid) + '.jpg'
