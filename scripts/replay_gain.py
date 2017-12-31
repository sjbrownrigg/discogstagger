import os, errno, sys, fnmatch

import logging
import subprocess

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

  cmd = []
  cmd.append("metaflac")
  cmd.append("--preserve-modtime")
  cmd.append("--add-replay-gain")

  subdirs = next(os.walk(albumdir))[1]

  pattern = albumdir
  if not subdirs:
    pattern = pattern + "/*.flac"
  else:
    pattern = pattern + "/**/*.flac"

  cmd.append(pattern)

  line = subprocess.list2cmdline(cmd)
  p = subprocess.Popen(line, shell=True)
  return_code = p.wait()
  logging.debug("return %s" % str(return_code))

logging.debug('added replay gain tags to %d albums' % len(albums))
