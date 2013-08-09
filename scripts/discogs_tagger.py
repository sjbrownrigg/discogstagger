#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import errno
import shutil
import logging
import sys
import imghdr
import glob
import ConfigParser
from optparse import OptionParser
from ext.mediafile import MediaFile
from discogstagger.taggerutils import (
    TaggerUtils,
    create_nfo,
    create_m3u,
    get_images)
from discogstagger.tagger_config import TaggerConfig

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

p.set_defaults(conffile="/etc/discogstagger/discogs_tagger.conf")
(options, args) = p.parse_args()

if not options.sourcedir or not os.path.exists(options.sourcedir):
    p.error("Please specify a valid source directory ('-s')")

tagger_config = TaggerConfig()
tagger_config.read(options.conffile)

logging.basicConfig(level=tagger_config.getint("logging", "level"))
logger = logging.getLogger(__name__)

# read necessary config options for batch processing
id_file = config.get("batch", "id_file")
dir_format_batch = "dir"
dir_format = None

# read tags from batch file if available
tagger_config.read(os.path.join(options.sourcedir, id_file))

if config.get("source", "id"):
    releaseid = config.get("source", "id").strip()

# command line parameter overwrites config parameter in file
if options.releaseid:
    releaseid = options.releaseid

if not releaseid:
    p.error("Please specify the discogs.com releaseid ('-r')")

# read destination directory
if not options.destdir:
    destdir = options.sdir
else:
    destdir = options.destdir
    logger.info("destdir set to %s", options.destdir)

logger.info("Using destination directory: %s", destdir)

discogs_album = DiscogsAlbum(self.ogsrelid, tagger_config)
album = discogs_album.map()

taggerutils = TaggerUtils(options.sourcedir, options.destdir, releaseid,
                          tagger_config, album)

# !TODO - make this a check during the taggerutils run
# ensure we were able to map the release appropriately.
#if not release.tag_map:
#    logger.error("Unable to match file list to discogs release '%s'" %
#                  releaseid)
#    sys.exit()

logger.info("Tagging album '%s - %s'" % (artist, release.album.title))

dest_dir_name = release.dest_dir_name

# !TODO this needs to get "fixed" to allow tagging already existing files
if os.path.exists(dest_dir_name):
    logger.error("Destination already exists %s" % dest_dir_name)
    sys.exit("%s directory already exists, aborting." % dest_dir_name)
else:
    logger.info("Creating destination directory '%s'" % dest_dir_name)
    mkdir_p(dest_dir_name)

logger.info("Downloading and storing images")
taggerutils.get_images(dest_dir_name)

    # it does not make sense to store this in the "common" configuration, but only in the 
    # id.txt. we use a special naming convention --> most probably we should reuse the 
    # configuration parser for this one as well, no?
    for name, value in release_tags.items():
        if name.startswith("tag:"):
            name = name.split(":")
            name = name[1]
            setattr(metadata, name, value)

#
# start supplementary actions
#
# adopt for multi disc support (copy to disc folder, add disc number, ...)
logger.info("Generating .nfo file")
create_nfo(release.album.album_info, dest_dir_name, release.nfo_filename)

# adopt for multi disc support
logger.info("Generating .m3u file")
create_m3u(release.tag_map, folder_names, dest_dir_name, release.m3u_filename)


logger.info("Tagging complete.")
