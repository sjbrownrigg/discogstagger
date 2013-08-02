#!/usr/bin/python
# -*- coding: utf-8 -*-
import os, sys
import shutil
from nose.tools import *

from ext.mediafile import MediaFile

import logging

logging.basicConfig(level=10)
logger = logging.getLogger(__name__)

parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parentdir)

logger.debug("parentdir: %s" % parentdir)

from _common_test import DummyResponse, DummyDiscogsAlbum

from discogstagger.tagger_config import TaggerConfig
from discogstagger.discogsalbum import DiscogsAlbum
from discogstagger.taggerutils import TaggerUtils, TagHandler, FileHandler

class TaggerUtilsBase(object):

    def setUp(self):
        self.ogsrelid = "1448190"

        # construct config with only default values
        self.tagger_config = TaggerConfig(os.path.join(parentdir, "test/empty.conf"))

        dummy_response = DummyResponse(self.ogsrelid)
        discogs_album = DummyDiscogsAlbum(self.ogsrelid, self.tagger_config, dummy_response)
        self.album = discogs_album.map()

    def tearDown(self):
        self.ogsrelid = None
        self.tagger_config = None
        self.config = None
        self.album = None

class TestTaggerUtils(TaggerUtilsBase):

    def test_value_from_tag_format(self):
        taggerutils = TaggerUtils("dummy_source_dir", "dummy_dest_dir", self.ogsrelid,
                                  self.tagger_config, self.album)

        format = taggerutils._value_from_tag_format("%DISCNO%", 1, 1, ".mp3")
        assert format == "1"

        format = taggerutils._value_from_tag_format("%ALBARTIST%-%ALBTITLE%")
        assert format == "Various-Megahits 2001 Die Erste"

        format = taggerutils._value_from_tag_format("%ALBARTIST%-%ALBTITLE%-(%CATNO%)-%YEAR%")
        assert format == "Various-Megahits 2001 Die Erste-(560 938-2)-2001"

        format = taggerutils._value_from_tag_format("%TRACKNO%-%ARTIST%-%TITLE%%TYPE%")
        assert format == "01-Gigi D'Agostino-La Passion (Radio Cut).mp3"

        format = taggerutils._value_from_tag_format("%TRACKNO%-%ARTIST%-%TITLE%", 1, 1, ".flac")
        assert format == "01-Gigi D'Agostino-La Passion (Radio Cut)"

    def test_value_from_tag(self):
        taggerutils = TaggerUtils("dummy_source_dir", "dummy_dest_dir", self.ogsrelid,
                                  self.tagger_config, self.album)

        format = taggerutils._value_from_tag("%ALBARTIST%-%ALBTITLE%")
        assert format == "various-megahits_2001_die_erste"

        format = taggerutils._value_from_tag("%ALBARTIST%-%ALBTITLE%-(%CATNO%)-%YEAR%")
        assert format == "various-megahits_2001_die_erste-(560_938-2)-2001"

        format = taggerutils._value_from_tag("%TRACKNO%-%ARTIST%-%TITLE%%TYPE%")
        assert format == "01-gigi_dagostino-la_passion_(radio_cut).mp3"

        format = taggerutils._value_from_tag("%TRACKNO%-%ARTIST%-%TITLE%", 1, 1, ".flac")
        assert format == "01-gigi_dagostino-la_passion_(radio_cut)"

    def test_dest_dir_name(self):
        taggerutils = TaggerUtils("dummy_source_dir", "./dummy_dest_dir", self.ogsrelid,
                                  self.tagger_config, self.album)
        assert taggerutils.dest_dir_name == "dummy_dest_dir/various-megahits_2001_die_erste-(560_938-2)-2001"

        taggerutils = TaggerUtils("dummy_source_dir", "dummy_dest_dir", self.ogsrelid,
                                  self.tagger_config, self.album)
        assert taggerutils.dest_dir_name == "dummy_dest_dir/various-megahits_2001_die_erste-(560_938-2)-2001"

        taggerutils = TaggerUtils("dummy_source_dir", "/dummy_dest_dir", self.ogsrelid,
                                  self.tagger_config, self.album)
        assert taggerutils.dest_dir_name == "/dummy_dest_dir/various-megahits_2001_die_erste-(560_938-2)-2001"

        taggerutils = TaggerUtils("dummy_source_dir", "dummy_dest_dir", self.ogsrelid,
                                  self.tagger_config, self.album)
        taggerutils.dir_format = "%GENRE%/%ALBARTIST%/%ALBTITLE%-(%CATNO%)-%YEAR%"
        assert taggerutils.dest_dir_name == "dummy_dest_dir/electronic/various/megahits_2001_die_erste-(560_938-2)-2001"


class TestTaggerUtilFiles(TaggerUtilsBase):

    def setUp(self):
        TaggerUtilsBase.setUp(self)

        self.source_dir = "/tmp/dummy_source_dir"
        self.target_dir = "/tmp/dummy_dest_dir"

        self.source_file = "test/files/test.flac"
        self.source_copy_file = "test/files/test.txt"

        os.mkdir(self.source_dir)
        os.mkdir(self.target_dir)

    def tearDown(self):
        TaggerUtilsBase.tearDown(self)

        # we are removing this directory in one test (see FileHandler)
        # therefor we need to be cautious ;-)
        if os.path.exists(self.source_dir):
            shutil.rmtree(self.source_dir)
        shutil.rmtree(self.target_dir)

    def test__get_target_list_multi_disc(self):
        # copy file to source directory and rename it
        for dir in range(1, 3):
            dir_name = "disc%d" % dir
            multi_source_dir = os.path.join(self.source_dir, dir_name)
            logger.debug("multi source dir: %s" % multi_source_dir)
            os.mkdir(multi_source_dir)

            for i in range(1, 21):
                target_file_name = "%.2d-song.flac" % i
                shutil.copyfile(self.source_file, os.path.join(multi_source_dir, target_file_name))

            target_file_name = "album.m3u"
            shutil.copyfile(self.source_copy_file, os.path.join(multi_source_dir, target_file_name))

            target_file_name = "album.cue"
            shutil.copyfile(self.source_copy_file, os.path.join(multi_source_dir, target_file_name))

        target_file_name = "id.txt"
        shutil.copyfile(self.source_copy_file, os.path.join(self.source_dir, target_file_name))

        taggerutils = TaggerUtils(self.source_dir, self.target_dir, self.ogsrelid,
                                  self.tagger_config, self.album)

        taggerutils._get_target_list()

        assert self.album.copy_files[0] == "id.txt"

        assert self.album.sourcedir == self.source_dir
        assert self.album.discs[0].sourcedir == "disc1"
        assert self.album.discs[1].sourcedir == "disc2"

        assert self.album.target_dir == self.target_dir

        assert self.album.discs[0].target_dir == "megahits_2001_die_erste-disc1"
        assert self.album.discs[1].target_dir == "megahits_2001_die_erste-disc2"

        assert self.album.discs[0].copy_files[0] == "album.cue"
        assert self.album.discs[0].copy_files[1] == "album.m3u"

        assert self.album.discs[1].copy_files[0] == "album.cue"
        assert self.album.discs[1].copy_files[1] == "album.m3u"

        assert self.album.discs[0].tracks[0].orig_file == "01-song.flac"
        assert self.album.discs[0].tracks[0].new_file == "01-gigi_dagostino-la_passion_(radio_cut).flac"

        assert self.album.discs[0].tracks[19].orig_file == "20-song.flac"
        assert self.album.discs[0].tracks[19].new_file == "20-papa_roach-last_resort_(album_version_explizit).flac"

        assert self.album.discs[1].tracks[0].orig_file == "01-song.flac"
        assert self.album.discs[1].tracks[0].new_file == "01-die_3_generation-ich_will_dass_du_mich_liebst_(radio_edit).flac"

        assert self.album.discs[1].tracks[19].orig_file == "20-song.flac"
        assert self.album.discs[1].tracks[19].new_file == "20-jay-z-i_just_wanna_love_u_(give_it_2_me)_(radio_edit).flac"

    def test__get_target_list_single_disc(self):
        self.ogsrelid = "3083"

        # construct config with only default values
        tagger_config = TaggerConfig(os.path.join(parentdir, "test/empty.conf"))
        self.config = tagger_config.config

        dummy_response = DummyResponse(self.ogsrelid)
        discogs_album = DummyDiscogsAlbum(self.ogsrelid, tagger_config, dummy_response)
        self.album = discogs_album.map()

        # copy file to source directory and rename it
        for i in range(1, 18):
            target_file_name = "%.2d-song.flac" % i
            shutil.copyfile(self.source_file, os.path.join(self.source_dir, target_file_name))

        target_file_name = "album.m3u"
        shutil.copyfile(self.source_copy_file, os.path.join(self.source_dir, target_file_name))

        target_file_name = "album.cue"
        shutil.copyfile(self.source_copy_file, os.path.join(self.source_dir, target_file_name))

        target_file_name = "id.txt"
        shutil.copyfile(self.source_copy_file, os.path.join(self.source_dir, target_file_name))

        taggerutils = TaggerUtils(self.source_dir, self.target_dir, self.ogsrelid,
                                  self.tagger_config, self.album)

        taggerutils._get_target_list()

        assert self.album.sourcedir == self.source_dir
        assert self.album.discs[0].sourcedir == None

        assert self.album.target_dir == self.target_dir
        assert self.album.discs[0].target_dir == None

        assert self.album.discs[0].tracks[0].orig_file == "01-song.flac"
        assert self.album.discs[0].tracks[0].new_file == "01-yonderboi-intro.flac"

        assert self.album.discs[0].tracks[16].orig_file == "17-song.flac"
        assert self.album.discs[0].tracks[16].new_file == "17-yonderboi-outro.flac"

        assert self.album.discs[0].copy_files[0] == "album.cue"
        assert self.album.discs[0].copy_files[1] == "album.m3u"
        assert self.album.discs[0].copy_files[2] == "id.txt"

    def test__create_file_from_template(self):
        self.ogsrelid = "3083"

        # construct config with only default values
        tagger_config = TaggerConfig(os.path.join(parentdir, "test/empty.conf"))
        self.config = tagger_config.config

        dummy_response = DummyResponse(self.ogsrelid)
        discogs_album = DummyDiscogsAlbum(self.ogsrelid, tagger_config, dummy_response)
        self.album = discogs_album.map()

        taggerutils = TaggerUtils(self.source_dir, self.target_dir, self.ogsrelid,
                                  self.tagger_config, self.album)

        create_file = os.path.join(self.target_dir, "info.nfo")
        assert taggerutils.create_file_from_template("/info.txt", create_file)

        assert os.path.exists(create_file)

        assert taggerutils.create_nfo(self.target_dir)

        # copy file to source directory and rename it
        for i in range(1, 18):
            target_file_name = "%.2d-song.flac" % i
            shutil.copyfile(self.source_file, os.path.join(self.source_dir, target_file_name))

        target_file_name = "album.m3u"
        shutil.copyfile(self.source_copy_file, os.path.join(self.source_dir, target_file_name))

        target_file_name = "album.cue"
        shutil.copyfile(self.source_copy_file, os.path.join(self.source_dir, target_file_name))

        target_file_name = "id.txt"
        shutil.copyfile(self.source_copy_file, os.path.join(self.source_dir, target_file_name))

        taggerutils = TaggerUtils(self.source_dir, self.target_dir, self.ogsrelid,
                                  self.tagger_config, self.album)

        taggerutils._get_target_list()
        assert self.album.discs[0].tracks[0].new_file == "01-yonderboi-intro.flac"
        assert taggerutils.create_m3u(self.target_dir)

class TestFileHandler(TestTaggerUtilFiles):

    def setUp(self):
        TestTaggerUtilFiles.setUp(self)
        self.target_file_name = "test.flac"

    def tearDown(self):
        TestTaggerUtilFiles.tearDown(self)
        self.tagger_config = None

    def test_remove_source_dir(self):
        self.album.sourcedir = self.source_dir

        assert self.tagger_config.getboolean("details", "keep_original")

        testFileHandler = FileHandler(self.album, self.tagger_config)

        target_file = os.path.join(self.album.sourcedir, "id.txt")
        shutil.copyfile(self.source_copy_file, target_file)

        assert os.path.exists(target_file)

        testFileHandler.remove_source_dir()

        assert os.path.exists(self.album.sourcedir)
        assert os.path.exists(target_file)

        # construct config with only default values
        self.tagger_config = TaggerConfig(os.path.join(parentdir, "test/test_values.conf"))

        assert not self.tagger_config.getboolean("details", "keep_original")

        testFileHandler = FileHandler(self.album, self.tagger_config)

        assert os.path.exists(target_file)

        testFileHandler.remove_source_dir()

        assert not os.path.exists(self.album.sourcedir)
        assert not os.path.exists(target_file)


class TestTagHandler(TestTaggerUtilFiles):

    def setUp(self):
        TestTaggerUtilFiles.setUp(self)
        self.target_file_name = "test.flac"

    def tearDown(self):
        TestTaggerUtilFiles.tearDown(self)

    def test_tag_single_track(self):
        shutil.copyfile(self.source_file, os.path.join(self.source_dir, self.target_file_name))

        testTagHandler = TagHandler(self.album, self.tagger_config)
        self.album.disc(1).track(1).new_file = self.target_file_name

        testTagHandler.tag_single_track(self.source_dir, self.album.disc(1).track(1))

        metadata = MediaFile(os.path.join(self.source_dir, self.target_file_name))

        assert metadata.artist == "Gigi D'Agostino"
        assert metadata.albumartist == "Various"
        assert metadata.discogs_id == self.ogsrelid
        assert metadata.year == 2001
        assert metadata.disctotal == 2
        assert metadata.comp
        assert metadata.genre == "Electronic & Hip Hop & Pop & Rock"

        assert metadata.freedb_id == "4711"

        # obviously the encoder element is not in the file, but it is returned
        # empty anyway, no need to check this then...
        assert metadata.encoder == ""

        # use a different file to check other metadata handling (e.g. artist)
        shutil.copyfile(self.source_file, os.path.join(self.source_dir, self.target_file_name))

        testTagHandler = TagHandler(self.album, self.tagger_config)
        self.album.disc(2).track(19).new_file = self.target_file_name

        testTagHandler.tag_single_track(self.source_dir, self.album.disc(2).track(19))

        metadata = MediaFile(os.path.join(self.source_dir, self.target_file_name))

        logger.debug("artist: %s" % metadata.artist_sort)
        assert metadata.artist == "D-Flame Feat. Eißfeldt"
        assert metadata.artist_sort == "D-Flame"
        assert metadata.discogs_id == self.ogsrelid
        assert metadata.year == 2001
        assert metadata.disctotal == 2
        assert metadata.disc == 2
        assert metadata.track == 19
        assert metadata.comp
        assert metadata.genre == "Electronic & Hip Hop & Pop & Rock"

        # obviously the encoder element is not in the file, but it is returned
        # empty anyway, no need to check this then...
        assert metadata.encoder == ""

    def test_tag_album(self):
        for dir in range(1, 3):
            dir_name = "disc%d" % dir
            multi_source_dir = os.path.join(self.source_dir, dir_name)
            logger.debug("multi source dir: %s" % multi_source_dir)
            os.mkdir(multi_source_dir)

            for i in range(1, 21):
                target_file_name = "%.2d-song.flac" % i
                shutil.copyfile(self.source_file, os.path.join(multi_source_dir, target_file_name))

        taggerutils = TaggerUtils(self.source_dir, self.target_dir, self.ogsrelid,
                                  self.tagger_config, self.album)

        taggerutils._get_target_list()

        testTagHandler = TagHandler(self.album, self.tagger_config)
        testFileHandler = FileHandler(self.album, self.tagger_config)

        testFileHandler.copy_files()

        testTagHandler.tag_album()

        target_dir = os.path.join(self.target_dir, self.album.target_dir, self.album.disc(1).target_dir)
        metadata = MediaFile(os.path.join(target_dir, "01-gigi_dagostino-la_passion_(radio_cut).flac"))

        assert metadata.artist == "Gigi D'Agostino"
        assert metadata.albumartist == "Various"
        assert metadata.discogs_id == self.ogsrelid
        assert metadata.year == 2001
        assert metadata.disctotal == 2
        assert metadata.comp
        assert metadata.genre == "Electronic & Hip Hop & Pop & Rock"

        assert metadata.freedb_id == "4711"

        # obviously the encoder element is not in the file, but it is returned
        # empty anyway, no need to check this then...
        assert metadata.encoder == ""

        metadata = MediaFile(os.path.join(target_dir, "20-papa_roach-last_resort_(album_version_explizit).flac"))

        logger.debug("artist: %s" % metadata.artist_sort)
        assert metadata.artist == "Papa Roach"
        assert metadata.artist_sort == "Papa Roach"
        assert metadata.discogs_id == self.ogsrelid
        assert metadata.year == 2001
        assert metadata.disctotal == 2
        assert metadata.disc == 1
        assert metadata.track == 20
        assert metadata.comp
        assert metadata.genre == "Electronic & Hip Hop & Pop & Rock"

        # obviously the encoder element is not in the file, but it is returned
        # empty anyway, no need to check this then...
        assert metadata.encoder == ""
