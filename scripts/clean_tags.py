import os, errno, sys, fnmatch

import logging
import subprocess

from mutagen.flac import FLAC

from optparse import OptionParser

logging.basicConfig(level=10)
logger = logging.getLogger(__name__)

def find_files(basepath, pattern):
    result = []

    logging.debug('migration starts in %s for files %s' % (basepath, pattern))

    base = os.path.expanduser(basepath)

    for root, dirs, files in os.walk(base):
            for filename in fnmatch.filter(files, pattern):
                    result.append(os.path.join(root, filename))

    return result

p = OptionParser()
p.add_option("-b", "--basedir", action="store", dest="basedir",
             help="The (base) directory to search for id files to migrate")
(options, args) = p.parse_args()

if not options.basedir:
  p.print_help()
  sys.exit(1)

logging.debug('starting migration')
files = find_files(options.basedir, "*.flac")

logging.debug('migrate %d files' % len(files))

filenames = []
for filename in files:
    logging.debug("working on %s" % filename)

    audio = FLAC(filename)

    cmd = []

    cmd.append("metaflac")
    cmd.append("--preserve-modtime")
    cmd.append("--remove-tag=TRACK")
    cmd.append("--remove-tag=TRACKC")
    cmd.append("--remove-tag=TOTALTRACKS")
    cmd.append("--remove-tag=DISC")
    cmd.append("--remove-tag=DISCC")
    cmd.append("--remove-tag=TOTALDISCS")
    cmd.append("--remove-tag=ALBUM ARTIST")
    cmd.append("--remove-tag=PUBLISHER")
    cmd.append("--remove-tag=ENCODEDBY")
    cmd.append("--remove-tag=DESCRIPTION")
    cmd.append("--remove-tag=URL")
    cmd.append("--remove-tag=URLTAG")

    discogsId = None
    if 'discogs_id' in audio:
        discogsId = audio['discogs_id']

        cmd.append("--remove-tag=discogs_id")
        cmd.append("--set-tag=DISCOGSID=" + ''.join(str(e) for e in discogsId))
        cmd.append("--set-tag=URL_DISCOGS_RELEASE_SITE=https://www.discogs.com/release/" + ''.join(str(e) for e in discogsId))

    cmd.append(filename)

    logging.debug("cmd %s" % cmd)

    p = subprocess.Popen(cmd)
    return_code = p.wait()
    logging.debug("return %s" % str(return_code))

    filenames.append(filename)

logging.debug('migrated %d files' % (len(filenames)))
