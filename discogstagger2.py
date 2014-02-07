#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import errno
import logging
import sys

from optparse import OptionParser

from discogstagger.tagger_config import TaggerConfig
from discogstagger.discogsalbum import DiscogsAlbum, DiscogsConnector
from discogstagger.taggerutils import TaggerUtils, TagHandler, FileHandler

import os, errno

def read_id_file(dir, file_name, options):
    # read tags from batch file if available
    idfile = os.path.join(dir, file_name)
    if os.path.exists(idfile):
        logger.debug("reading id file %s in %s" % (file_name, dir))
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

logging.basicConfig(level=tagger_config.getint("logging", "level"))
logger = logging.getLogger(__name__)

# read necessary config options for batch processing
id_file = tagger_config.get("batch", "id_file")

if options.recursive:
    logger.debug("determine sourcedirs")
    source_dirs = walk_dir_tree(options.sourcedir, id_file)
else:
    logger.debug("using sourcedir: %s" % options.sourcedir)
    source_dirs = [options.sourcedir]

logger.debug("starting tagging")
for source_dir in source_dirs:
    done_file = tagger_config.get("details", "done_file")
    done_file_path = os.path.join(source_dir, done_file)
    if os.path.exists(done_file_path) and not options.forceUpdate:
        logger.info("Do not read %s, because %s exists and forceUpdate is false" % (source_dir, done_file))
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
        logger.info("destdir set to %s", options.destdir)

    logger.info("Using destination directory: %s", destdir)

    logger.info("starting tagging...")
    discogs_connector = DiscogsConnector(tagger_config)
    release = discogs_connector.fetch_release(releaseid)
    discogs_album = DiscogsAlbum(release)

    album = discogs_album.map()

    logger.info("Tagging album '%s - %s'" % (album.artist, album.title))

    taggerUtils = TaggerUtils(source_dir, destdir, tagger_config, album)

    tagHandler = TagHandler(album, tagger_config)
    fileHandler = FileHandler(album, tagger_config)

    taggerUtils._get_target_list()

    fileHandler.copy_files()

    logger.info("Tagging files")
    tagHandler.tag_album()

    logger.info("Copy other interesting files (on request)")
    fileHandler.copy_other_files()

    logger.info("Downloading and storing images")
    fileHandler.get_images(discogs_connector)

    logger.info("Embedding Albumart")
    fileHandler.embed_coverart_album()

# !TODO make this more generic to use different templates and files,
# furthermore adopt to reflect multi-disc-albums
    logger.info("Generate m3u")
    taggerUtils.create_m3u(album.target_dir)

    logger.info("Generate nfo")
    taggerUtils.create_nfo(album.target_dir)

    fileHandler.create_done_file()

    # !TODO - make this a check during the taggerutils run
    # ensure we were able to map the release appropriately.
    #if not release.tag_map:
    #    logger.error("Unable to match file list to discogs release '%s'" %
    #                  releaseid)
    #    sys.exit()

logger.info("Tagging complete.")
