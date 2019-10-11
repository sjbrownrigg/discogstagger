# -*- coding: utf-8 -*-
# from urllib import FancyURLopener
import errno
import os
import re
import sys
import logging
import shutil
import imghdr

import pprint
pp = pprint.PrettyPrinter(indent=4)

from unicodedata import normalize

from mako.template import Template
from mako.lookup import TemplateLookup

from discogstagger.discogsalbum import DiscogsAlbum
from discogstagger.album import Album, Disc, Track
from discogstagger.stringformatting import StringFormatting

from ext.mediafile import MediaFile

# commenting these out (python3)
# reload(sys)
# sys.setdefaultencoding("utf-8")

logger = logging

# class TagOpener(FancyURLopener, object):
#
#     version = "discogstagger2"
#
#     def __init__(self, user_agent):
#         self.version = user_agent
#         FancyURLopener.__init__(self)
#
class TaggerError(Exception):
    """ A central exception for all errors happening during the tagging
    """
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)

class TagHandler(object):
    """ Uses the album (taggerutils) and tags all given files using the given
        tags (album)
    """

    def __init__(self, album, tagger_config):
        self.album = album
        self.config = tagger_config

        self.keep_tags = self.config.get("details", "keep_tags")
        self.user_agent = self.config.get("common", "user_agent")

    def tag_album(self):
        """ tags all tracks in an album, the filenames are determined using
            the given properties on the tracks
        """
        for disc in self.album.discs:
            if disc.target_dir != None:
                target_folder = os.path.join(self.album.target_dir, disc.target_dir)
            else:
                target_folder = self.album.target_dir

            for track in disc.tracks:
                self.tag_single_track(target_folder, track)

    def tag_single_track(self, target_folder, track):
        # load metadata information
        logger.debug("target_folder: %s" % target_folder)

        metadata = MediaFile(os.path.join(target_folder, track.new_file))

        # read already existing (and still wanted) properties
        keepTags = {}
        for name in self.keep_tags.split(","):
            logger.debug("name %s" % name)
            if getattr(metadata, name):
                keepTags[name] = getattr(metadata, name)

        # remove current metadata
        metadata.delete()

        self.album.codec = metadata.type

        # set album metadata
        metadata.album = self.album.title
        metadata.composer = self.album.artist

        # use list of albumartists
        metadata.albumartists = self.album.artists

# !TODO really, or should we generate this using a specific method?
        metadata.albumartist_sort = self.album.sort_artist

# !TODO should be joined
        metadata.label = self.album.labels[0]

        metadata.year = self.album.year
        metadata.country = self.album.country

        metadata.catalognum = self.album.catnumbers[0]

        # add styles to the grouping tag
        metadata.groupings = self.album.styles

        # use genres to allow multiple genres in muliple fields
        metadata.genres = self.album.genres

        # this assumes, that there is a metadata-tag with the id_tag_name in the
        # metadata object
        setattr(metadata, self.config.id_tag_name, self.album.id)
        metadata.discogs_release_url = self.album.url

        metadata.disc = track.discnumber
        metadata.disctotal = len(self.album.discs)

        if self.album.is_compilation:
            metadata.comp = True

        metadata.comments = self.album.notes

        tags = self.config.get_configured_tags
        logger.debug("tags: %s" % tags)
        for name in tags:
            value = self.config.get("tags", name)
            if not value == None:
                setattr(metadata, name, value)

        # set track metadata
        metadata.title = track.title
        metadata.artists = track.artists

# !TODO take care about sortartist ;-)
        metadata.artist_sort = track.sort_artist
        metadata.track = track.tracknumber

        metadata.tracktotal = len(self.album.disc(track.discnumber).tracks)

        if not keepTags is None:
            for name in keepTags:
                setattr(metadata, name, keepTags[name])

        metadata.save()

class FileHandler(object):
    """ this class contains all file handling tasks for the tagger,
        it loops over the album and discs (see copy_files) to copy
        the files for each album. This could be done in the TagHandler
        class, but this would mean a too strong relationship between
        FileHandling and Tagging, which is not as nice for testing and
        for future extensability.
    """


    def __init__(self, album, tagger_config):
        self.config = tagger_config
        self.album = album

    def mkdir_p(self, path):
        try:
            os.makedirs(path)
        except OSError as exc: # Python >2.5
            if exc.errno == errno.EEXIST and os.path.isdir(path):
                pass
            else: raise

    def create_done_file(self):
        # could be, that the directory does not exist anymore ;-)
        if os.path.exists(self.album.sourcedir):
            done_file = os.path.join(self.album.sourcedir, self.config.get("details", "done_file"))
            open(done_file, "w")

    def create_album_dir(self):
        if not os.path.exists(self.album.target_dir):
            self.mkdir_p(self.album.target_dir)

    def copy_files(self):
        """
            copy an album and all its files to the new location, rename those
            files if necessary
        """
        logger.debug("album sourcedir: %s" % self.album.sourcedir)
        logger.debug("album targetdir: %s" % self.album.target_dir)

        for disc in self.album.discs:
            logger.debug("disc.sourcedir: %s" % disc.sourcedir)
            logger.debug("disc.target_dir: %s" % disc.target_dir)

            if disc.sourcedir != None:
                source_folder = os.path.join(self.album.sourcedir, disc.sourcedir)
            else:
                source_folder = self.album.sourcedir

            if disc.target_dir != None:
                target_folder = os.path.join(self.album.target_dir, disc.target_dir)
            else:
                target_folder = self.album.target_dir

            copy_needed = False
            if not source_folder == target_folder:
                if not os.path.exists(target_folder):
                    self.mkdir_p(target_folder)
                copy_needed = True

            for track in disc.tracks:
                logger.debug("source_folder: %s" % source_folder)
                logger.debug("target_folder: %s" % target_folder)
                logger.debug("orig_file: %s" % track.orig_file)
                logger.debug("new_file: %s" % track.new_file)

                source_file = os.path.join(source_folder, track.orig_file)
                target_file = os.path.join(target_folder, track.new_file)

                if copy_needed and not os.path.exists(target_file):
                    if not os.path.exists(source_file):
                        logger.error("Source does not exists")
                        # throw error
                    logger.debug("copying files (%s/%s)", source_folder, track.orig_file)

                    shutil.copyfile(os.path.join(source_folder, track.orig_file),
                        os.path.join(target_folder, track.new_file))

    def remove_source_dir(self):
        """
            remove source directory, if configured as such (see config option
            details:keep_original)
        """
        keep_original = self.config.getboolean("details", "keep_original")
        source_dir = self.album.sourcedir

        logger.debug("keep_original: %s" % keep_original)
        logger.debug("going to remove directory....")
        if not keep_original:
            logger.warn("Deleting source directory '%s'" % source_dir)
            shutil.rmtree(source_dir)

    def copy_other_files(self):
        # copy "other files" on request
        copy_other_files = self.config.getboolean("details", "copy_other_files")

        if copy_other_files:
            logger.info("copying files from source directory")

            if not os.path.exists(self.album.target_dir):
                self.mkdir_p(self.album.target_dir)

            copy_files = self.album.copy_files

            if copy_files != None:
                for fname in copy_files:
                    shutil.copyfile(os.path.join(self.album.sourcedir, fname), os.path.join(self.album.target_dir, fname))

            for disc in self.album.discs:
                copy_files = disc.copy_files

                for fname in copy_files:
                    if not fname.endswith(".m3u"):
                        if disc.sourcedir != None:
                            source_path = os.path.join(self.album.sourcedir, disc.sourcedir)
                        else:
                            source_path = self.album.sourcedir

                        if disc.target_dir != None:
                            target_path = os.path.join(self.album.target_dir, disc.target_dir)
                        else:
                            target_path = self.album.target_dir

                        if not os.path.exists(target_path):
                            self.mkdir_p(target_path)
                        shutil.copyfile(os.path.join(source_path, fname), os.path.join(target_path, fname))

    def get_images(self, conn_mgr):
        """
            Download and store any available images
            The images are all copied into the album directory, on multi-disc
            albums the first image (mostly folder.jpg) is copied into the
            disc directory also to make it available to mp3 players (e.g. deadbeef)

            we need http access here as well (see discogsalbum), and therefore the
            user-agent
        """
        if self.album.images:
            images = self.album.images

            logger.debug("images: %s" % images)

            image_format = self.config.get("file-formatting", "image")
            use_folder_jpg = self.config.getboolean("details", "use_folder_jpg")
            download_only_cover = self.config.getboolean("details", "download_only_cover")

            logger.debug("image-format: %s" % image_format)
            logger.debug("use_folder_jpg: %s" % use_folder_jpg)

            self.create_album_dir()

            no = 0
            for i, image_url in enumerate(images, 0):
                logger.debug("Downloading image '%s'" % image_url)
                try:
                    picture_name = ""
                    if i == 0 and use_folder_jpg:
                        picture_name = "folder.jpg"
                    else:
                        no = no + 1
                        picture_name = image_format + "-%.2d.jpg" % no

                    conn_mgr.fetch_image(os.path.join(self.album.target_dir, picture_name), image_url)

                    if i == 0 and download_only_cover:
                        break

                except Exception as e:
                    logger.error("Unable to download image '%s', skipping." % image_url)
                    print(e)

    def embed_coverart_album(self):
        """
            Embed cover art into all album files
        """
        embed_coverart = self.config.getboolean("details", "embed_coverart")
        image_format = self.config.get("file-formatting", "image")
        use_folder_jpg = self.config.getboolean("details", "use_folder_jpg")

        if use_folder_jpg:
            first_image_name = "folder.jpg"
        else:
            first_image_name = image_format + "-01.jpg"

        image_file = os.path.join(self.album.target_dir, first_image_name)

        logger.debug("Start to embed coverart (on request)...")

        if embed_coverart and os.path.exists(image_file):
            logger.debug("embed_coverart and image_file")
            imgdata = open(image_file).read()
            imgtype = imghdr.what(None, imgdata)#

            if imgtype in ("jpeg", "png"):
                logger.info("Embedding album art...")
                for disc in self.album.discs:
                    for track in disc.tracks:
                        self.embed_coverart_track(disc, track, imgdata)

    def embed_coverart_track(self, disc, track, imgdata):
        """
            Embed cover art into a single file
        """
        if disc.target_dir != None:
            track_dir = os.path.join(self.album.target_dir, disc.target_dir)
        else:
            track_dir = self.album.target_dir

        track_file = os.path.join(track_dir, track.new_file)
        metadata = MediaFile(track_file)
        metadata.art = imgdata
        metadata.save()

    def add_replay_gain_tags(self):
        """
            Add replay gain tags to all flac files in the given directory.

            Uses the default metaflac command, therefor this has to be installed
            on your system, to be able to use this method.
        """
        cmd = []
        cmd.append("metaflac")
        cmd.append("--preserve-modtime")
        cmd.append("--add-replay-gain")

        albumdir = self.album.target_dir
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


class TaggerUtils(object):
    """ Accepts a destination directory name and discogs release id.
        TaggerUtils returns a the corresponding metadata information, in which
        we can write to disk. The assumption here is that the destination
        direcory contains a single album in a support format (mp3 or flac).

        The class also provides a few methods that create supplimental files,
        relvant to a given album (m3u, nfo file and album art grabber.)"""

    # supported file types.
    FILE_TYPE = (".mp3", ".flac",)

    def __init__(self, sourcedir, destdir, tagger_config, album=None):
        self.config = tagger_config

        # ignore directory where old cue files are stashed
        self.cue_done_dir = self.config.get('cue', 'cue_done_dir')

# !TODO should we define those in here or in each method (where needed) or in a separate method
# doing the "mapping"?
        self.dir_format = self.config.get("file-formatting", "dir")
        self.song_format = self.config.get("file-formatting", "song")
        self.va_song_format = self.config.get("file-formatting", "va_song")
        self.images_format = self.config.get("file-formatting", "image")
        self.m3u_format = self.config.get("file-formatting", "m3u")
        self.nfo_format = self.config.get("file-formatting", "nfo")

        self.disc_folder_name = self.config.get("file-formatting", "discs")

        self.use_lower = self.config.getboolean("details", "use_lower_filenames")

#        self.first_image_name = "folder.jpg"
        self.copy_other_files = self.config.getboolean("details", "copy_other_files")
        self.char_exceptions = self.config.get_character_exceptions

        self.sourcedir = sourcedir
        self.destdir = destdir

        if not album == None:
            self.album = album
        else:
            raise RuntimeException('Cannot tag, no album given')

        self.album.sourcedir = sourcedir
        # the album is stored in a directory beneath the destination directory
        # and following the given dir_format
        self.album.target_dir = self.dest_dir_name

        logging.debug("album.target_dir: %s" % self.dest_dir_name)

        # add template functionality ;-)
        self.template_lookup = TemplateLookup(directories=["templates"])

    def _value_from_tag_format(self, format, discno=1, trackno=1, filetype=".mp3"):
        """ Fill in the used variables using the track information
            Transform all variables and use them in the given format string, make this
            slightly more flexible to be able to add variables easier

            Transfer this via a map.
        """

        property_map = {

            '%album artist%': self.album.artist,
            '%albumartist%': self.album.artist,
            '%album%': self.album.title,
            "%year%": self.album.year,
            '%artist%': self.album.disc(discno).track(trackno).artist,
            '%discnumber%':discno,
            '%totaldiscs%':'',
            '%track artist%': self.album.disc(discno).track(trackno).artist,
            '%title%': self.album.disc(discno).track(trackno).title,
            '%tracknumber%': "%.2d" % trackno,
            '%track number%': "%.2d" % trackno,
            "%fileext%": filetype,
            '%bitrate%':'',
            '%channels%':'',
            '%codec%': self.album.codec,
            '%filesize%':'',
            '%filesize_natural%':'',
            '%length%':'',
            '%length_ex%':'',
            '%length_seconds%':'',
            '%length_seconds_fp%':'',
            '%length_samples%':'',
            '%samplerate%':self.album.codec,

            "%ALBTITLE%": self.album.title,
            "%ALBARTIST%": self.album.artist,
            "%YEAR%": self.album.year,
            "%CATNO%": self.album.catnumbers[0],
            "%GENRE%": self.album.genre,
            "%STYLE%": self.album.style,
            "%ARTIST%": self.album.disc(discno).track(trackno).artist,
            "%TITLE%": self.album.disc(discno).track(trackno).title,
            "%DISCNO%": discno,
            "%TRACKNO%": "%.2d" % trackno,
            "%TYPE%": filetype,
            "%LABEL%": self.album.labels[0],
            "%CODEC%": self.album.codec,
        }

        for hashtag in property_map.keys():
            format = format.replace(hashtag, str(property_map[hashtag]))

        return format

    def _value_from_tag(self, format, discno=1, trackno=1, filetype=".mp3"):
        """ Generates the filename tagging map
            avoid usage of file extension here already, could lead to problems
        """

        print('_value_from_tag')
        stringFormatting = StringFormatting()
        format = self._value_from_tag_format(format, discno, trackno, filetype)
        format = stringFormatting.parseString(format)
        format = self.get_clean_filename(format)

        print(format)

        logger.debug("output: %s" % format)

        return format

    def _set_target_discs_and_tracks(self, filetype):
        """
            set the target names of the disc and tracks in the discnumber
            based on the configuration settings and the name of the disc
            or track
            these can be calculated without knowing the source (well, the
            filetype seems to be a different calibre)
        """

        for disc in self.album.discs:
            if not self.album.has_multi_disc:
                disc.target_dir = None
            else:
                disc.target_dir = self.get_clean_filename(self._value_from_tag_format(self.disc_folder_name, disc.discnumber))

            for track in disc.tracks:
                # special handling for Various Artists discs
                if self.album.artist == "Various":
                    newfile = self._value_from_tag(self.va_song_format, disc.discnumber,
                                               track.tracknumber, filetype)
                else:
                    newfile = self._value_from_tag(self.song_format, disc.discnumber,
                                               track.tracknumber, filetype)

                track.new_file = self.get_clean_filename(newfile)

    def gather_addional_properties(self):
        ''' Fetches additional technical information about the tracks
        '''
        for disc in self.album.discs:
            for track in disc.tracks:
                metadata = MediaFile(track.full_path)
                for field in metadata.readable_fields():
                    print('fieldname: {}: {}'.format(field, getattr(metadata, field)))

                self.album.codec = metadata.type
                self.album.samplerate = metadata.samplerate
                self.album.bitrate = metadata.bitrate
                self.album.bitdepth = metadata.bitdepth



    def _get_target_list(self):
        """
            fetches a list of files with the defined file_type
            in the self.sourcedir location as target_list, other
            files in the sourcedir are returned in the copy_files list.
        """
        copy_files = []
        target_list = []

        print('_get_target_list')

        sourcedir = self.album.sourcedir

        logger.debug("target_dir: %s" % self.album.target_dir)
        logger.debug("sourcedir: %s" % sourcedir)

        try:
            dir_list = os.listdir(sourcedir)
            dir_list.sort()

            print(dir_list)

            # self.cue_done_dir = '.cue'
            extf = (self.cue_done_dir)
            dir_list[:] = [d for d in dir_list if d not in extf]

            filetype = ""
            print(dir_list)

            self.album.copy_files = []

            if self.album.has_multi_disc:
                print('album identified as having multiple discs')
                logger.debug("is multi disc album, looping discs")

                logger.debug("dir_list: %s" % dir_list)
                dirno = 0
                for y in dir_list:
                    logger.debug("is it a dir? %s" % y)
                    if os.path.isdir(os.path.join(sourcedir, y)):
                        logger.debug("Setting disc(%s) sourcedir to: %s" % (dirno, y))
                        self.album.discs[dirno].sourcedir = y
                        dirno = dirno + 1
                    else:
                        logger.debug("Setting copy_files instead of sourcedir")
                        self.album.copy_files.append(y)
            else:
                logger.debug("Setting disc sourcedir to none")
                self.album.discs[0].sourcedir = None

            for disc in self.album.discs:
                print('going through disc')
                try:
                    disc_source_dir = disc.sourcedir
                except AttributeError:
                    logger.error("there seems to be a problem in the meta-data, check if there are sub-tracks")
                    raise TaggerError("no disc sourcedir defined, does this release contain sub-tracks?")

                if disc_source_dir == None:
                    disc_source_dir = self.album.sourcedir

                print(disc_source_dir)
                logger.debug("discno: %d" % disc.discnumber)
                logger.debug("sourcedir: %s" % disc.sourcedir)

                # strip unwanted files
                disc_list = os.listdir(disc_source_dir)
                print(disc_list)
                disc_list.sort()

                print('disc_list.sort')

                disc.copy_files = [x for x in disc_list
                                if not x.lower().endswith(TaggerUtils.FILE_TYPE)]

                target_list = [os.path.join(disc_source_dir, x) for x in disc_list
                                 if x.lower().endswith(TaggerUtils.FILE_TYPE)]

                print(target_list)

                if not len(target_list) == len(disc.tracks):
                    logger.debug("target_list: %s" % target_list)
                    logger.error("not matching number of files....")
                    # we should throw an error in here

                for position, filename in enumerate(target_list):
                    logger.debug("track position: %d" % position)

                    print('position: {}'.format(position))
                    print('filename: {}'.format(filename))

                    track = disc.tracks[position]

                    logger.debug("mapping file %s --to--> %s - %s" % (filename,
                                 track.artists[0], track.title))

                    track.orig_file = os.path.basename(filename)
                    # multidisc target path is in filename, not track.orig_file
                    # track.full_path = self.album.sourcedir + track.orig_file
                    track.full_path = os.path.join(self.album.sourcedir, filename)
                    filetype = os.path.splitext(filename)[1]

            self._set_target_discs_and_tracks(filetype)

        except (OSError) as e:
            if e.errno == errno.EEXIST:
                logger.error("No such directory '%s'", self.sourcedir)
                raise TaggerError("No such directory '%s'", self.sourcedir)
            else:
                raise TaggerError("General IO system error '%s'" % errno[e])

    @property
    def dest_dir_name(self):
        """ generates new album directory name """

        logger.debug("self.destdir: %s" % self.destdir)

        # determine if an absolute base path was specified.
        path_name = os.path.normpath(self.destdir)

        logger.debug("path_name: %s" % path_name)

        dest_dir = ""
        for ddir in self.dir_format.split("/"):
            d_dir = self.get_clean_filename(self._value_from_tag(ddir))
            if dest_dir == "":
                dest_dir = d_dir
            else:
                dest_dir = os.path.join(dest_dir, d_dir)

            logger.debug("d_dir: %s" % dest_dir)

        dir_name = os.path.join(path_name, dest_dir)

        return dir_name

    @property
    def m3u_filename(self):
        """ generates the m3u file name """

        m3u = self._value_from_tag(self.m3u_format)
        return self.get_clean_filename(m3u)

    @property
    def nfo_filename(self):
        """ generates the nfo file name """

        nfo = self._value_from_tag(self.nfo_format)
        return self.get_clean_filename(nfo)


    def get_clean_filename(self, f):
        """ Removes unwanted characters from file names """

        filename, fileext = os.path.splitext(f)

        print('get_clean_filename')

        if not fileext in TaggerUtils.FILE_TYPE and not fileext in [".m3u", ".nfo"]:
            logger.debug("fileext: %s" % fileext)
            filename = f
            fileext = ""


        print(filename)
        a = str(filename)
        print(a)


        for k, v in self.char_exceptions.items():
            a = a.replace(k, v)

        a = normalize("NFKD", a)
        print(a)

        cf = re.compile(r"[^-\w.\(\)_\[\]\s]")
        cf = cf.sub("", str(a))

        print(cf)
        # Don't force space/underscore replacement. If the user want's this it
        # can be done via config. The user may want spaces.
        # cf = cf.replace(" ", "_")
        # cf = cf.replace("__", "_")
        # cf = cf.replace("_-_", "-")

        cf = "".join([cf, fileext])

        if self.use_lower:
            cf = cf.lower()

        print(cf)

        return cf

    def create_file_from_template(self, template_name, file_name):
        file_template = self.template_lookup.get_template(template_name)
        return write_file(file_template.render(album=self.album),
            os.path.join(self.album.target_dir, file_name))

    def create_nfo(self, dest_dir):
        """ Writes the .nfo file to disk. """
        return self.create_file_from_template("info.txt", self.nfo_filename)

    def create_m3u(self, dest_dir):
        """ Generates the playlist for the given albm.
            Adhering to the following m3u format.

            ---
            #EXTM3U
            #EXTINF:233,Artist - Song
            directory\file_name.mp3.mp3
            #EXTINF:-1,My Cool Stream
            http://www.site.com:8000/listen.pls
            ---

            Taken from http://forums.winamp.com/showthread.php?s=&threadid=65772"""
        return self.create_file_from_template("m3u.txt", self.m3u_filename)


def write_file(filecontents, filename):
    """ writes a string of data to disk """

    if not os.path.exists(os.path.dirname(filename)):
        os.makedirs(os.path.dirname(filename))

    logger.debug("Writing file '%s' to disk" % filename)

    try:
        with open(filename, "w") as fh:
            fh.write(filecontents)
    except IOError:
        logger.error("Unable to write file '%s'" % filename)

    return True
