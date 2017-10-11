import os, errno, sys, fnmatch

import shutil
import fileinput

import logging

from mutagen.flac import FLAC

from optparse import OptionParser

logging.basicConfig(filename="multi_discs.log", level=10)
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
  audio = FLAC(filename)

  artist_count = 0
  album_artist_count = 0
  albumartist_count = 0

  isDirty = False

  if 'artist' in audio:
    for name in audio['artist']:
      artist_count += 1

  if 'album artist' in audio:
    for name in audio['album artist']:
      album_artist_count += 1

  if 'albumartist' in audio:
    for name in audio['albumartist']:
        albumartist_count += 1


  if artist_count == 1 and albumartist_count > 1:
    logging.debug('file found: %s' % filename)

  isDirty = False

logging.debug('found %d artists and %d album_artists' % (artist_count, album_artist_count))

