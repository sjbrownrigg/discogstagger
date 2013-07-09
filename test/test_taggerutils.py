#!/usr/bin/python
# -*- coding: utf-8 -*-
import os, sys
import logging

logging.basicConfig(level=10)
logger = logging.getLogger(__name__)

parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parentdir)

logger.debug("parentdir: %s" % parentdir)

from _common_test import DummyResponse, DummyDiscogsAlbum

from discogstagger.tagger_config import TaggerConfig
from discogstagger.discogsalbum import DiscogsAlbum
from discogstagger.taggerutils import TaggerUtils

def test_value_from_tag_format():
    ogsrelid = "1448190"

    # construct config with only default values
    tagger_config = TaggerConfig(os.path.join(parentdir, "test/empty.conf"))
    config = tagger_config.config

    dummy_response = DummyResponse(ogsrelid)
    discogs_album = DummyDiscogsAlbum(ogsrelid, dummy_response)
    album = discogs_album.map()

    taggerutils = TaggerUtils("dummy_source_dir", "dummy_dest_dir", ogsrelid,
                              config, album)

    format = taggerutils._value_from_tag_format("%DISCNO%", 1, 1, 1, ".mp3")
    assert format == "1"

    format = taggerutils._value_from_tag_format("%ALBARTIST%-%ALBTITLE%")
    assert format == "Various-Megahits 2001 Die Erste"

    format = taggerutils._value_from_tag_format("%ALBARTIST%-%ALBTITLE%-(%CATNO%)-%YEAR%")
    assert format == "Various-Megahits 2001 Die Erste-(560 938-2)-Germany"

    format = taggerutils._value_from_tag_format("%TRACKNO%-%ARTIST%-%TITLE%%TYPE%")
    assert format == "01-Gigi D'Agostino-La Passion (Radio Cut).mp3"

    format = taggerutils._value_from_tag_format("%TRACKNO%-%ARTIST%-%TITLE%", 1, 1, 1, ".flac")
    assert format == "01-Gigi D'Agostino-La Passion (Radio Cut)"

def test_value_from_tag():
    ogsrelid = "1448190"

    # construct config with only default values
    tagger_config = TaggerConfig(os.path.join(parentdir, "test/empty.conf"))
    config = tagger_config.config

    dummy_response = DummyResponse(ogsrelid)
    discogs_album = DummyDiscogsAlbum(ogsrelid, dummy_response)
    album = discogs_album.map()

    taggerutils = TaggerUtils("dummy_source_dir", "dummy_dest_dir", ogsrelid,
                              config, album)

    format = taggerutils._value_from_tag("%ALBARTIST%-%ALBTITLE%")
    assert format == "various-megahits_2001_die_erste"

    format = taggerutils._value_from_tag("%ALBARTIST%-%ALBTITLE%-(%CATNO%)-%YEAR%")
    assert format == "various-megahits_2001_die_erste-(560_938-2)-germany"

    format = taggerutils._value_from_tag("%TRACKNO%-%ARTIST%-%TITLE%%TYPE%")
    assert format == "01-gigi_dagostino-la_passion_(radio_cut).mp3"

    format = taggerutils._value_from_tag("%TRACKNO%-%ARTIST%-%TITLE%", 1, 1, 1, ".flac")
    assert format == "01-gigi_dagostino-la_passion_(radio_cut)"

    assert False