import os, errno, sys

import shutil
import fileinput

import logging

from optparse import OptionParser

logging.basicConfig(level=10)
logger = logging.getLogger(__name__)

def find_files(basepath, name):
		result = []

		logging.debug('migration starts in %s for files %s' % (basepath, name))

		base = os.path.expanduser(basepath)

		for root, dirs, files in os.walk(base):
				if name in files:
						result.append(os.path.join(root, name))
						logger.debug("added file: %s" % name)

		return result

def copy_file(name):
		logger.debug("copy file: %s" % name)
		logger.debug("target: %s" % os.path.join(os.path.dirname(name), "%s.orig" % os.path.basename(name)))
		shutil.copyfile(name, os.path.join(os.path.dirname(name), "%s.orig" % os.path.basename(name)))

def parse_file(name):
		logger.debug("parsing file: %s" % name)
		for line in fileinput.input(name, inplace=True):
				if "#Automatic migration from migrate_id_files" in line:
						fileinput.close()
						return
				if "discogs_id=" in line:
						line = line.replace("discogs_id=", "#Automatic migration from migrate_id_files\n[source]\ndiscogs_id=")
						sys.stdout.write(line)
                        fileinput.close()

p = OptionParser()
p.add_option("-b", "--basedir", action="store", dest="basedir",
             help="The (base) directory to search for id files to migrate")
(options, args) = p.parse_args()


logging.debug('starting migration')
files = find_files(options.basedir, "id.txt")

logging.debug('migrate %d files' % len(files))

for filename in files:
		copy_file(filename)
		parse_file(filename)
