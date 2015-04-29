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

if not options.basedir:
  p.print_help()
  sys.exit(1)

logging.debug('starting migration')
files = find_files(options.basedir, "*.flac")

logging.debug('migrate %d files' % len(files))

filenames = []
for filename in files:
	audio = FLAC(filename)

	genres = []
	artists = []
	albumArtists = []
	albumArtists_ = []

	isDirty = False
	if 'genre' in audio:
		for name in audio['genre']:
			if '\\\\' in name:
				isDirty = True
				split = name.split('\\\\')
				for name2 in split:
					genres.append(name2)
			else:
				genres.append(name)

	for index, name in enumerate(genres):
		fixname = name
		if 'Hip-Hop' == fixname:
			isDirty = True
			genres[index] = 'Hip Hop'
		elif 'Folk, World, & Country' == fixname:
			isDirty = True
			genres[index] = 'Folk, World & Country'


	if 'artist' in audio:
		for name in audio['artist']:
			if '\\\\' in name:
				isDirty = True
				split = name.split('\\\\')
				for name2 in split:
					artists.append(name2)
			else:
				artists.append(name)

	if 'album artist' in audio:
		for name in audio['album artist']:
			if '\\\\' in name:
				isDirty = True
				split = name.split('\\\\')
				for name2 in split:
					albumArtists.append(name2)
			else:
				albumArtists.append(name)

	if 'albumartist' in audio:
		for name in audio['albumartist']:
			if '\\\\' in name:
				isDirty = True
				split = name.split('\\\\')
				for name2 in split:
					albumArtists_.append(name2)
			else:
				albumArtists_.append(name)

	if isDirty:
#		logging.debug('migrated %s with new tags (Genre: %s), (Artists: %s)' % (filename, genres, artists))
		audio['GENRE'] = genres
		audio['ARTIST'] = artists
		audio['ALBUM ARTIST'] = albumArtists
		audio['ALBUMARTIST'] = albumArtists_
		filenames.append(filename)

		audio.save()

	isDirty = False

logging.debug('migrated %d files: %s' % (len(filenames), filenames))

