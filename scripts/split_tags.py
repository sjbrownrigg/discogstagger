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
(options, args) = p.parse_args()

logging.debug('starting migration')
files = find_files(options.basedir, "*.flac")

logging.debug('migrate %d files' % len(files))

filenames = []
for filename in files:
	audio = FLAC(filename)

	genres = []
	artists = []
	isDirty = False
	for genrename in audio['genre']:
		if '\\\\' in genrename:
			isDirty = True
			genresplit = genrename.split('\\\\')
			for genrename2 in genresplit:
				genres.append(genrename2)
		else:
			genres.append(genrename)

	for artistname in audio['artist']:
		if '\\\\' in artistname:
			isDirty = True
			artistsplit = artistname.split('\\\\')
			for artistname2 in artistsplit:
				artists.append(artistname2)
		else:
			artists.append(artistname)

	if isDirty:
		logging.debug('migrated %s with new tags (Genre: %s), (Artists: %s)' % (filename, genres, artists))
		audio['genre'] = genres
		audio['artist'] = artists
		filenames.append(filename)

		audio.save()

	isDirty = False

logging.debug('migrated %d files: %s' % (len(filenames), filenames))

