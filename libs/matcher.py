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
    status = ""

    def __init__(self, list_cr, list_mid):
        """
        Runs matching on received lists.
        """
        self.list_cr = list_cr
        self.list_mid = list_mid

    def get_matches(self):
        start = time.time()
        results = self.match(self.list_cr, self.list_mid)
        match_took = time.time() - start

        log.debug("Matching took {}.".format(self.readable_time(match_took)))

        return results, self.status

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

        mat = np.zeros([len(imgs_cr), len(imgs_api)])
        for i in range(len(imgs_cr)):
            for j in range(len(imgs_api)):
                mat[i][j] = self.dist(imgs_cr[i], imgs_api[j])

        return mat

    def match(self, list_cr, list_mid):
        """
        Generates dictionary of cr_ids matching mids.
        """
        mat = self.matrix(list_cr, list_mid)

        minima_locations = self.get_minima(mat)

        out = {}
        for i in range(len(minima_locations)):
            out[list_cr[i]] = list_mid[minima_locations[i]]

        return out

    def get_minima(self, mat):
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

        if unambiguous:
            self.status = 1
        else:
            self.status = 0
            log.info("Some matches are ambiguous.")
            for i in range(len(occurences)):
                try:
                    for candidate in occurences[i]:
                        # TODO Not sure which index is which - might be switched CR/API
                        log.info(
                            "Ambiguous candidate: {} -> {}".format(self.list_cr[i], self.list_mid[candidate]))
                except:
                    pass

        max_difference = np.max(minima)
        if max_difference < 5:
            log.debug("Maximum difference in images was {}.".format(max_difference))
        else:
            log.info("WARNING! Maximum difference {} >= 5. Trouble?".format(max_difference))

        # debug
        log.debug("Matrix:")
        for row in mat:
            log.debug(row)
        log.debug("Minima_locations:")
        log.debug(minima_locations)
        log.debug("Minima:")
        log.debug(minima)
        log.debug("Occurences:")
        log.debug(occurences)

        return minima_locations

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
                log.info("URLError, trouble...")
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
