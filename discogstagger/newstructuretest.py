# -*- coding: utf-8 -*-

from urllib import FancyURLopener
import os
import re
import sys
import logging
import inspect
from unicodedata import normalize

from discogsalbum import DiscogsAlbum

reload(sys)
sys.setdefaultencoding("utf-8")

logging.basicConfig(level=10)
logger = logging.getLogger(__name__)

ogsrelid = "1448190"

discogs_album = DiscogsAlbum(ogsrelid)

logger.debug(inspect.getmembers(discogs_album.release))

logger.debug(requests.get("http://api.discogs.com/release/1448190", params={}, headers={ 'accept-encoding': 'gzip, deflate', 'user-header' : 'discogstagger2 +http://github.com/triplem' }))

album = discogs_album.map()


logger.debug("album.labels: %s" % album.labels)
logger.debug("album.catnumbers: %s" % album.catnumbers)
logger.debug("album.images %s" % album.images)