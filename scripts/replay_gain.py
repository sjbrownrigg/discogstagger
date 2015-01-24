import os, errno, sys, fnmatch

import shutil
import fileinput

import logging
import subprocess
import pipes

from optparse import OptionParser

logging.basicConfig(level=10)
logger = logging.getLogger(__name__)

def find_files(basepath, pattern):
  result = []

  base = os.path.expanduser(basepath)

  for root, dirs, files in os.walk(base):
    for filename in fnmatch.filter(files, pattern):
      result.append(os.path.join(root))

  return result

p = OptionParser()
p.add_option("-b", "--basedir", action="store", dest="basedir",
             help="The (base) directory to search for id files to migrate")
(options, args) = p.parse_args()

if not options.basedir:
  p.print_help()
  sys.exit(1)

albums = find_files(options.basedir, "id.txt")

logging.debug('add replay gain tags to %d albums' % len(albums))

for albumdir in albums:
  tag_folders = []

  for dirpath, dirnames, files in os.walk(albumdir):
    for filename in fnmatch.filter(files, "*.flac"):
      tag_folders.append(dirpath)
      break

  cmd = "metaflac --add-replay-gain"
  for folder in tag_folders:
    cmd = cmd + " \"" + folder + "\"/*.flac"

  p = subprocess.Popen(cmd, shell=True)
  (output, err) = p.communicate()
  logging.debug("%s" % output)

logging.debug('added replay gain tags to %d albums' % len(albums))
