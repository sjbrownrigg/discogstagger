#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import errno
import logging
import logging.config
import sys

from optparse import OptionParser

from discogstagger.tagger_config import TaggerConfig
from discogstagger.discogsalbum import DiscogsAlbum, DiscogsConnector, LocalDiscogsConnector, AlbumError
from discogstagger.taggerutils import TaggerUtils, TagHandler, FileHandler, TaggerError

import os, errno

def read_id_file(dir, file_name, options):
    # read tags from batch file if available
    idfile = os.path.join(dir, file_name)
    if os.path.exists(idfile):
        logger.info("reading id file %s in %s" % (file_name, dir))
        tagger_config.read(idfile)
        source_type = tagger_config.get("source", "name")
        id_tag_name = tagger_config.get("source", source_type)
        releaseid = tagger_config.get("source", id_tag_name)
    elif options.releaseid:
        releaseid = options.releaseid

    return releaseid

def walk_dir_tree(start_dir, id_file):
    source_dirs = []
    for root, dirs, files in os.walk(start_dir):
        if id_file in files:
            logger.debug("found %s in %s" % (id_file, root))
            source_dirs.append(root)

    return source_dirs

p = OptionParser(version="discogstagger2 0.9")
p.add_option("-r", "--releaseid", action="store", dest="releaseid",
             help="The release id of the target album")
p.add_option("-s", "--source", action="store", dest="sourcedir",
             help="The directory that you wish to tag")
p.add_option("-d", "--destination", action="store", dest="destdir",
             help="The (base) directory to copy the tagged files to")
p.add_option("-c", "--conf", action="store", dest="conffile",
             help="The discogstagger configuration file.")
p.add_option("--recursive", action="store_true", dest="recursive",
             help="Should albums be searched recursive in the source directory?")
p.add_option("-f", "--force", action="store_true", dest="forceUpdate",
             help="Should albums be updated even though the done token exists?")

p.set_defaults(conffile="conf/empty.conf")
p.set_defaults(recursive=False)
p.set_defaults(forceUpdate=False)

if len(sys.argv) == 1:
    p.print_help()
    sys.exit(1)

(options, args) = p.parse_args()

if not options.sourcedir or not os.path.exists(options.sourcedir):
    p.error("Please specify a valid source directory ('-s')")

tagger_config = TaggerConfig(options.conffile)

# initialize logging
logger_config_file = tagger_config.get("logging", "config_file")
logging.config.fileConfig(logger_config_file)

logger = logging.getLogger(__name__)

# read necessary config options for batch processing
id_file = tagger_config.get("batch", "id_file")

if options.recursive:
    logger.debug("determine sourcedirs")
    source_dirs = walk_dir_tree(options.sourcedir, id_file)
else:
    logger.debug("using sourcedir: %s" % options.sourcedir)
    source_dirs = [options.sourcedir]

# initialize connection (could be a problem if using multiple sources...)
discogs_connector = DiscogsConnector(tagger_config)
local_discogs_connector = LocalDiscogsConnector(discogs_connector)

logger.info("start tagging")
discs_with_errors = []

converted_discs = 0

releaseid = None

for source_dir in source_dirs:
    try:
        done_file = tagger_config.get("details", "done_file")
        done_file_path = os.path.join(source_dir, done_file)

        if os.path.exists(done_file_path) and not options.forceUpdate:
            logger.warn("Do not read %s, because %s exists and forceUpdate is false" % (source_dir, done_file))
            continue

        # reread config to make sure, that the album specific options are reset for each
        # album
        tagger_config = TaggerConfig(options.conffile)

        releaseid = read_id_file(source_dir, id_file, options)


        if not releaseid:
            p.error("Please specify the discogs.com releaseid ('-r')")

        # read destination directory
        # !TODO if both are the same, we are not copying anything,
        # this should be "configurable"
        if not options.destdir:
            destdir = source_dir
        else:
            destdir = options.destdir
            logger.debug("destdir set to %s", options.destdir)

        logger.info("Using destination directory: %s", destdir)

        logger.debug("starting tagging...")

        #! TODO this is dirty, refactor it to be able to reuse it for later enhancements
        if tagger_config.get("source", "name") == "local":
            release = local_discogs_connector.fetch_release(releaseid, source_dir)
            connector = local_discogs_connector
        else:
            release = discogs_connector.fetch_release(releaseid)
            connector = discogs_connector

        discogs_album = DiscogsAlbum(release)

        try:
            album = discogs_album.map()
        except AlbumError as ae:
            msg = "Error during mapping ({0}), {1}: {2}".format(releaseid, source_dir, ae)
            logger.error(msg)
            discs_with_errors.append(msg)
            continue

        logger.info("Tagging album '%s - %s'" % (album.artist, album.title))

        taggerUtils = TaggerUtils(source_dir, destdir, tagger_config, album)

        tagHandler = TagHandler(album, tagger_config)
        fileHandler = FileHandler(album, tagger_config)

        try:
            taggerUtils._get_target_list()
        except TaggerError as te:
            msg = "Error during Tagging ({0}), {1}: {2}".format(releaseid, source_dir, te)
            logger.error(msg)
            discs_with_errors.append(msg)
            continue

        fileHandler.copy_files()

        logger.debug("Tagging files")
        tagHandler.tag_album()

        logger.debug("Copy other interesting files (on request)")
        fileHandler.copy_other_files()

        logger.debug("Downloading and storing images")
        fileHandler.get_images(connector)

        logger.debug("Embedding Albumart")
        fileHandler.embed_coverart_album()

    # !TODO make this more generic to use different templates and files,
    # furthermore adopt to reflect multi-disc-albums
        logger.debug("Generate m3u")
        taggerUtils.create_m3u(album.target_dir)

        logger.debug("Generate nfo")
        taggerUtils.create_nfo(album.target_dir)

        fileHandler.create_done_file()
    except Exception as ex:
        if releaseid:
            msg = "Error during tagging ({0}), {1}: {2}".format(releaseid, source_dir, ex)
        else:
            msg = "Error during tagging (no relid) {0}: {1}".format(source_dir, ex)
        logger.error(msg)
        discs_with_errors.append(msg)
        continue

    # !TODO - make this a check during the taggerutils run
    # ensure we were able to map the release appropriately.
    #if not release.tag_map:
    #    logger.error("Unable to match file list to discogs release '%s'" %
    #                  releaseid)
    #    sys.exit()
    converted_discs = converted_discs + 1
    logger.info("Converted %d/%d" % (converted_discs, len(source_dirs)))

logger.info("Tagging complete.")
logger.info("converted successful: %d" % converted_discs)
logger.info("converted with Errors %d" % len(discs_with_errors))
logger.info("releases touched: %s" % len(source_dirs))

if discs_with_errors:
    logger.error("The following discs could not get converted.")
    for msg in discs_with_errors:
        logger.error(msg)
