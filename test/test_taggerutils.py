#!/usr/bin/python
# -*- coding: utf-8 -*-
import os, sys
import shutil
from nose.tools import *

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


class TestTaggerUtils:

    def setUp(self):
        self.ogsrelid = "1448190"

        # construct config with only default values
        tagger_config = TaggerConfig(os.path.join(parentdir, "test/empty.conf"))
        self.config = tagger_config.config

        dummy_response = DummyResponse(self.ogsrelid)
        discogs_album = DummyDiscogsAlbum(self.ogsrelid, dummy_response)
        self.album = discogs_album.map()

    def tearDown(self):
        self.ogsrelid = None
        self.config = None
        self.album = None

    def test_value_from_tag_format(self):
        taggerutils = TaggerUtils("dummy_source_dir", "dummy_dest_dir", self.ogsrelid,
                                  self.config, self.album)

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

    def test_value_from_tag(self):
        taggerutils = TaggerUtils("dummy_source_dir", "dummy_dest_dir", self.ogsrelid,
                                  self.config, self.album)

        format = taggerutils._value_from_tag("%ALBARTIST%-%ALBTITLE%")
        assert format == "various-megahits_2001_die_erste"

        format = taggerutils._value_from_tag("%ALBARTIST%-%ALBTITLE%-(%CATNO%)-%YEAR%")
        assert format == "various-megahits_2001_die_erste-(560_938-2)-germany"

        format = taggerutils._value_from_tag("%TRACKNO%-%ARTIST%-%TITLE%%TYPE%")
        assert format == "01-gigi_dagostino-la_passion_(radio_cut).mp3"

        format = taggerutils._value_from_tag("%TRACKNO%-%ARTIST%-%TITLE%", 1, 1, 1, ".flac")
        assert format == "01-gigi_dagostino-la_passion_(radio_cut)"

    def test_dest_dir_name(self):
        taggerutils = TaggerUtils("dummy_source_dir", "./dummy_dest_dir", self.ogsrelid,
                                  self.config, self.album)
        assert taggerutils.dest_dir_name == "dummy_dest_dir/various-megahits_2001_die_erste-(560_938-2)-germany"

        taggerutils = TaggerUtils("dummy_source_dir", "dummy_dest_dir", self.ogsrelid,
                                  self.config, self.album)
        assert taggerutils.dest_dir_name == "dummy_dest_dir/various-megahits_2001_die_erste-(560_938-2)-germany"

        taggerutils = TaggerUtils("dummy_source_dir", "/dummy_dest_dir", self.ogsrelid,
                                  self.config, self.album)
        assert taggerutils.dest_dir_name == "/dummy_dest_dir/various-megahits_2001_die_erste-(560_938-2)-germany"

        taggerutils = TaggerUtils("dummy_source_dir", "dummy_dest_dir", self.ogsrelid,
                                  self.config, self.album)
        taggerutils.dir_format = "%GENRE%/%ALBARTIST%/%ALBTITLE%-(%CATNO%)-%YEAR%"
        assert taggerutils.dest_dir_name == "dummy_dest_dir/electronic/various/megahits_2001_die_erste-(560_938-2)-germany"


    def test_album_folder_name(self):
        taggerutils = TaggerUtils("dummy_source_dir", "dummy_dest_dir", self.ogsrelid,
                                  self.config, self.album)

        assert taggerutils.album_folder_name(1) == "megahits_2001_die_erste-disc1"
        assert taggerutils.album_folder_name(2) == "megahits_2001_die_erste-disc2"

    def test_get_target_list(self):
        source_dir = "/tmp/dummy_source_dir"
        target_dir = "/tmp/dummy_dest_dir"
        source_file = "test/files/test.flac"

        os.mkdir(source_dir)
        os.mkdir(target_dir)

        # copy file to source directory and rename it
        for i in range(1, 21):
            target_file_name = "%.2d-song.flac" % i
            logger.debug("file_name: %s" % target_file_name)
            shutil.copyfile(source_file, os.path.join(source_dir, target_file_name))

        taggerutils = TaggerUtils(source_dir, target_dir, self.ogsrelid,
                                  self.config, self.album)

        result = taggerutils._get_target_list()

        assert not result["target_list"] == None
        assert len(result["target_list"]) == 20

        assert result["copy_files"] == []

        shutil.rmtree(source_dir)
        shutil.rmtree(target_dir)