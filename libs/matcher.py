#!/usr/bin/env python
# -*- coding: utf-8 -

from PIL import Image
import imagehash
import requests
from io import BytesIO
import numpy as np


class Matcher:
    """
    Tries to match cards by image. #greatidea #notwaistingtimeatall
    """

    def __init__(self, list_cr, list_mid):
        """
        Runs matching on received lists.
        """

        self.match(list_cr, list_mid)

    def matrix(self, list_cr, list_mid):
        """
        Creates a nxn matrix with distances of all images to each other.
        """
        imgs_cr = [self.load_img(self.url_cr(id_cr)) for id_cr in list_cr]
        imgs_api = [self.load_img(self.url_api(mid)) for mid in list_mid]

        mat = np.zeros([len(imgs_cr), len(imgs_api)])
        for i in range(len(imgs_cr)):
            for j in range(len(imgs_api)):
                mat[i][j] = self.dist(imgs_cr[i], imgs_api[j])

        # print(mat)
        return mat

    def match(self, list_cr, list_mid):
        """
        Generates dictionary of cr_ids matching mids.
        """
        mat = self.matrix(list_cr, list_mid)

        minima = np.argmin(mat, axis=1)
        # print(minima)

        out = {}
        for i in range(len(minima)):
            out[list_cr[i]] = list_mid[minima[i]]

        print(out)
        return out

    def dist(self, image_1, image_2):
        """
        Calculates distance of two images.
        """
        hash_1 = imagehash.average_hash(image_1)
        # print(hash_1)

        hash_2 = imagehash.average_hash(image_2)
        # print(hash_2)

        #print(hash == hash_2)
        return hash_1 - hash_2

    def load_img(self, url):
        """
        Downloads the image on provided url and returns it as an Image object.
        """
        response = requests.get(url)
        img = Image.open(BytesIO(response.content))
        return img

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


m = Matcher(['SOI_L10', 'SOI_L13', 'SOI_L04', 'SOI_L07', 'SOI_L01'],
            [410052, 410055, 410058, 410061, 410064])
