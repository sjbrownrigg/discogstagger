import os, sys
import logging

logging.basicConfig(level=10)
logger = logging.getLogger(__name__)

parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parentdir)

logger.debug("parentdir: %s" % parentdir)

from discogstagger.tagger_config import TaggerConfig
from discogstagger.discogsalbum import DiscogsAlbum

class TestDiscogsAlbum(object):

    def test_oauth(self):
        logger.debug('testing oauth...')

        self.ogsrelid = "1448190"

        # construct config with only default values
        self.tagger_config = TaggerConfig(os.path.join(parentdir, "conf/discogs_tagger_triplem_new.conf"))

        discogs_album = DiscogsAlbum(self.ogsrelid, self.tagger_config)

        discogs_album.fetch_images()
