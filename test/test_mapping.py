import os, sys
import logging

logging.basicConfig(level=10)
logger = logging.getLogger(__name__)

parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parentdir)

logger.debug("parentdir: %s" % parentdir)

from discogstagger.discogsalbum import DiscogsAlbum

class DummyResponse:
    def __init__(self, releaseid):
        __location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
        json_file_name =  "%s/release.json" % releaseid
        json_file_path = os.path.join(__location__, json_file_name)
        json_file = open(json_file_path, "r")

        self.status_code = 200
        self.content = json_file.read()

def test_map():
    ogsrelid = "1448190"

    discogs_album = DiscogsAlbum(ogsrelid)
    # mock response, so that the unit tests do not ask for the http connection
    # every time
    discogs_album.release._cached_response = DummyResponse(ogsrelid)

    album = discogs_album.map()

    assert len(album.labels) == 1
    assert album.labels[0] == "Polystar"

    assert len(album.catnumbers) == len(album.labels)
    assert album.catnumbers[0] == "560 938-2"

    assert len(album.images) == 4
    assert album.images[0] == "http://api.discogs.com/image/R-1448190-1220476110.jpeg"

    assert len(album.artists) == 1
    assert album.artists[0] == "Various"

    assert len(album.genres) == 4

    assert len(album.styles) == 4

    assert album.is_compilation

    assert album.disctotal == 2
    assert len(album.discs) == album.disctotal

    assert len(album.discs[0].tracks) == 20
    assert len(album.discs[1].tracks) == 20

    track = album.discs[0].tracks[0]
    assert track.tracknumber == 1
    assert track.discnumber == 1

    logger.debug("album.labels: %s" % album.labels[0])
    logger.debug("album.catnumbers: %s" % album.catnumbers)
    logger.debug("album.images %s" % album.images)
    logger.debug("album.artists %s" % album.artists)
    logger.debug("album.title %s" % album.title)
    logger.debug("album.genres %s" % album.genres)
    logger.debug("album.styles %s" % album.styles)
    logger.debug("album.discs %s" % len(album.discs))
    logger.debug("album.discs[0].tracks %s" % len(album.discs[0].tracks))
    logger.debug("album.discs[1].tracks %s" % len(album.discs[1].tracks))
    logger.debug("track.title %s" % track.title)

# seems to be not working without internet connection
#    assert track.title == "La Passion (Radio Cut)"


    assert false