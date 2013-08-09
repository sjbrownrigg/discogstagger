#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import errno
import shutil
import logging
import sys
import imghdr
import glob

from optparse import OptionParser

from discogstagger.tagger_config import TaggerConfig
from discogstagger.discogsalbum import DiscogsAlbum
from discogstagger.taggerutils import TaggerUtils, TagHandler, FileHandler

import os, errno

p = OptionParser()
p.add_option("-r", "--releaseid", action="store", dest="releaseid",
             help="The discogs.com release id of the target album")
p.add_option("-s", "--source", action="store", dest="sourcedir",
             help="The directory that you wish to tag")
p.add_option("-d", "--destination", action="store", dest="destdir",
             help="The (base) directory to copy the tagged files to")
p.add_option("-c", "--conf", action="store", dest="conffile",
             help="The discogstagger configuration file.")

p.set_defaults(conffile="conf/empty.conf")
(options, args) = p.parse_args()

if not options.sourcedir or not os.path.exists(options.sourcedir):
    p.error("Please specify a valid source directory ('-s')")

print 'conffile: ' + options.conffile

tagger_config = TaggerConfig(options.conffile)

logging.basicConfig(level=tagger_config.getint("logging", "level"))
logger = logging.getLogger(__name__)

# read necessary config options for batch processing
id_file = tagger_config.get("batch", "id_file")

# read tags from batch file if available
idfile = os.path.join(options.sourcedir, id_file)
if os.path.exists(idfile):
    tagger_config.read(idfile)
# !TODO make the stripping automactically in the tagger_config
    releaseid = tagger_config.get("source", "id").strip()
elif options.releaseid:
    releaseid = options.releaseid

if not releaseid:
    p.error("Please specify the discogs.com releaseid ('-r')")

# read destination directory
# !TODO if both are the same, we are not copying anything, 
# this should be "configurable"
if not options.destdir:
    destdir = options.sourcedir
else:
    destdir = options.destdir
    logger.info("destdir set to %s", options.destdir)

logger.info("Using destination directory: %s", destdir)

logger.info("starting tagging...")
discogs_album = DiscogsAlbum(releaseid, tagger_config)
album = discogs_album.map()

logger.info("Tagging album '%s - %s'" % (album.artist, album.title))

taggerUtils = TaggerUtils(options.sourcedir, destdir, releaseid,
                          tagger_config, album)

tagHandler = TagHandler(album, tagger_config)
fileHandler = FileHandler(album, tagger_config)

taggerUtils._get_target_list()

logger.info("Tagging files")
tagHandler.tag_album()

logger.info("Copy other interesting files (on request)")
fileHandler.copy_other_files()

logger.info("Downloading and storing images")
fileHandler.get_images()


# !TODO - make this a check during the taggerutils run
# ensure we were able to map the release appropriately.
#if not release.tag_map:
#    logger.error("Unable to match file list to discogs release '%s'" %
#                  releaseid)
#    sys.exit()


#dest_dir_name = album.dest_dir_name

# !TODO this needs to get "fixed" to allow tagging already existing files
#if os.path.exists(dest_dir_name):
#    logger.error("Destination already exists %s" % dest_dir_name)
#    sys.exit("%s directory already exists, aborting." % dest_dir_name)
#else:
#    logger.info("Creating destination directory '%s'" % dest_dir_name)
#    mkdir_p(dest_dir_name)

    # it does not make sense to store this in the "common" configuration, but only in the 
    # id.txt. we use a special naming convention --> most probably we should reuse the 
    # configuration parser for this one as well, no?
# !TODO --- do not forget about this one
#    for name, value in release_tags.items():
#        if name.startswith("tag:"):
#            name = name.split(":")
#            name = name[1]
#            setattr(metadata, name, value)

#
# start supplementary actions
#
# adopt for multi disc support (copy to disc folder, add disc number, ...)
#logger.info("Generating .nfo file")
#create_nfo(release.album.album_info, dest_dir_name, release.nfo_filename)

# adopt for multi disc support
#logger.info("Generating .m3u file")
#create_m3u(release.tag_map, folder_names, dest_dir_name, release.m3u_filename)


logger.info("Tagging complete.")
