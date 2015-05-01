import os, errno, sys, fnmatch

import shutil
import fileinput

import logging

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
p.add_option("-f", "--force", action="store_true", dest="forceUpdate",
						 help="force the resetting of existing folder tags")
p.set_defaults(forceUpdate=False)

(options, args) = p.parse_args()

if not options.basedir:
  p.print_help()
  sys.exit(1)

logging.debug('start adding new tag folder (if not already existing)')
files = find_files(options.basedir, "*.flac")

logging.debug('adopted %d files' % len(files))

filenames = []
for filename in files:
	audio = FLAC(filename)

	if 'folder' in audio:
		if options.forceUpdate:
			logging.debug('deleting folder -- forceUpdate was chosen')
			del audio['folder']
		else:
			continue

	folder = ''
	if 'albumartist' in audio:
		if audio['albumartist'][0] == 'Various':
			folder = audio['album']
		else:
			folder = audio['albumartist'][0]

	if 'album' in audio:
		if audio['album'][0].startswith('DJ Kicks'):
			folder = 'DJ Kicks'
		elif audio['album'][0].startswith('DJ-Kicks'):
			folder = 'DJ Kicks'
		elif audio['album'][0].startswith('Another LateNight'):
			folder = 'Another LateNight'
		elif audio['album'][0].startswith('LateNight'):
			folder = 'Another LateNight'

	logging.debug('folder: %s' % folder)
	audio['FOLDER'] = folder
	filenames.append(filename)

	audio.save()

logging.debug('migrated %d files: %s' % (len(filenames), filenames))
