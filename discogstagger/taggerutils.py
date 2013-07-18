# -*- coding: utf-8 -*-

from urllib import FancyURLopener
import os
import re
import sys
import logging
from unicodedata import normalize

from mako.template import Template
from mako.lookup import TemplateLookup

from discogstagger.discogsalbum import DiscogsAlbum
from discogstagger.album import Album, Disc, Track

reload(sys)
sys.setdefaultencoding("utf-8")

logger = logging.getLogger(__name__)

class TagOpener(FancyURLopener, object):

    version = "discogstagger +http://github.com/jesseward"

    def __init__(self):
        FancyURLopener.__init__(self)


class TaggerUtils(object):
    """ Accepts a destination directory name and discogs release id.
        TaggerUtils returns a the corresponding metadata information , in which
        we can write to disk. The assumption here is that the destination
        direcory contains a single album in a support format (mp3 or flac).

        The class also provides a few methods that create supplimental files,
        relvant to a given album (m3u, nfo file and album art grabber.)"""

    CHAR_EXCEPTIONS = {
        "&": "and",
        " ": "_",
        "ö": "oe",
        "Ö": "Oe",
        "Ä": "Ae",
        "ä": "ae",
        "Ü": "Ue",
        "ü": "ue",
        ".": "_",
        "+": "_and_",
    }

    # supported file types.
    FILE_TYPE = (".mp3", ".flac",)

    def __init__(self, sourcedir, destdir, ogsrelid, config, album=None):
        self.config = config

# !TODO should we define those in here or in each method (where needed) or in a separate method
# doing the "mapping"?
        self.dir_format = config.get("file-formatting", "dir")
        self.song_format = config.get("file-formatting", "song")
        self.va_song_format = config.get("file-formatting", "va_song")
        self.images_format = config.get("file-formatting", "images")
        self.m3u_format = config.get("file-formatting", "m3u")
        self.nfo_format = config.get("file-formatting", "nfo")

        self.disc_folder_name = config.get("file-formatting", "discs")

        self.use_lower = config.getboolean("details", "use_lower_filenames")

#        self.first_image_name = "folder.jpg"
        self.copy_other_files = config.getboolean("file-formatting", "copy_other_files")

        self.sourcedir = sourcedir
        self.destdir = destdir

        if not album == None:
            self.album = album
        else:
            discogs_album = DiscogsAlbum(ogsrelid)
            self.album = discogs_album.map()

        self.album.sourcedir = sourcedir
        self.album.target_dir = self.destdir

        # add template functionality ;-)
        self.template_lookup = TemplateLookup(directories=["templates"])

    def _value_from_tag_format(self, format, discno=1, trackno=1, position=1, filetype=".mp3"):
        """ Fill in the used variables using the track information
            Transform all variables and use them in the given format string, make this
            slightly more flexible to be able to add variables easier

            Transfer this via a map.
        """
        property_map = {
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
        }

        for hashtag in property_map.keys():
            format = format.replace(hashtag, str(property_map[hashtag]))

        return format

    def _value_from_tag(self, format, discno=1, trackno=1, position=1, filetype=".mp3"):
        """ Generates the filename tagging map
            avoid usage of file extension here already, could lead to problems
        """
        format = self._value_from_tag_format(format, discno, trackno, position, filetype)
        format = self.get_clean_filename(format)

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
                                               track.tracknumber, 1, filetype)
                else:
                    newfile = self._value_from_tag(self.song_format, disc.discnumber,
                                               track.tracknumber, 1, filetype)

                track.new_file = self.get_clean_filename(newfile)


    def _get_target_list(self):
        """
            fetches a list of files with the defined file_type
            in the self.sourcedir location as target_list, other
            files in the sourcedir are returned in the copy_files list.
        """

        copy_files = []
        target_list = []

        sourcedir = self.album.sourcedir

        logger.debug("target_dir: %s" % self.album.target_dir)

        try:
            dir_list = os.listdir(sourcedir)
            dir_list.sort()

            if self.album.has_multi_disc:
                self.album.copy_files = []

                for i, y in enumerate(dir_list):
                    if os.path.isdir(os.path.join(sourcedir, y)):
                        self.album.discs[i].sourcedir = y
                    else:
                        self.album.copy_files.append(y)
            else:
                self.album.discs[0].sourcedir = None

            for disc in self.album.discs:
                disc_source_dir = disc.sourcedir

                if disc_source_dir == None:
                    disc_source_dir = self.album.sourcedir

                logger.debug("discno: %d" % disc.discnumber)
                logger.debug("sourcedir: %s" % disc.sourcedir)

                # strip unwanted files
                disc_list = os.listdir(os.path.join(self.album.sourcedir, disc_source_dir))
                disc_list.sort()

                disc.copy_files = [x for x in disc_list
                                if not x.lower().endswith(TaggerUtils.FILE_TYPE)]

                target_list = [os.path.join(disc_source_dir, x) for x in disc_list
                                 if x.lower().endswith(TaggerUtils.FILE_TYPE)]

                if not len(target_list) == len(disc.tracks):
                    logger.debug("target_list: %s" % target_list)
                    logger.error("not matching number of files....")
                    # we should throw an error in here

                for position, filename in enumerate(target_list):
                    logger.debug("track position: %d" % position)

                    track = disc.tracks[position]

                    logger.debug("mapping file %s --to--> %s - %s" % (filename,
                                 track.artists[0], track.title))
                    track.orig_file = os.path.basename(filename)

                    filetype = os.path.splitext(filename)[1]

            self._set_target_discs_and_tracks(filetype)

        except OSError, e:
            if e.errno == errno.EEXIST:
                logger.error("No such directory '%s'", self.sourcedir)
                raise IOError("No such directory '%s'", self.sourcedir)
            else:
                raise IOError("General IO system error '%s'" % errno[e])

    @property
    def dest_dir_name(self):
        """ generates new album directory name """

        logger.debug("self.destdir: %s" % self.destdir)

        # determine if an absolute base path was specified.
        path_name = os.path.normpath(self.destdir)

        logger.debug("path_name: %s" % path_name)

        dest_dir = ""
        for ddir in self.dir_format.split("/"):
            logger.debug("d_dir: %s" % ddir)
            d_dir = self.get_clean_filename(self._value_from_tag(ddir))
            if dest_dir == "":
                dest_dir = d_dir
            else:
                dest_dir = dest_dir + "/" + d_dir

            logger.debug("d_dir: %s" % dest_dir)

        dir_name = os.path.join(path_name, dest_dir)

        return dir_name

# !TODO use templates for the following methods, to be able to define different files
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

        if not fileext in TaggerUtils.FILE_TYPE and not fileext in [".m3u", ".nfo"]:
            logger.debug("fileext: %s" % fileext)
            filename = f
            fileext = ""

        a = unicode(filename, "utf-8")

        for k, v in TaggerUtils.CHAR_EXCEPTIONS.iteritems():
            a = a.replace(k, v)

        a = normalize("NFKD", a).encode("ascii", "ignore")

        cf = re.compile(r"[^-\w.\(\)_]")
        cf = cf.sub("", str(a))

        cf = cf.replace(" ", "_")
        cf = cf.replace("__", "_")
        cf = cf.replace("_-_", "-")

        cf = "".join([cf, fileext])

        if self.use_lower:
            cf = cf.lower()

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

def get_images(images, dest_dir_name, images_format, first_image_name):
    """ Download and store any available images
        we need http access here as well (see discogsalbum), and therefore the
        user-agent, we should be able to put this into a common object, ....
    """

    if images:
        for i, image in enumerate(images, 0):
            logger.debug("Downloading image '%s'" % image)
            try:
                url_fh = TagOpener()

                picture_name = ""
                if i == 0:
                    picture_name = first_image_name
                else:
                    picture_name = images_format + "-%.2d.jpg" % i

                url_fh.retrieve(image, os.path.join(dest_dir_name, picture_name))
            except Exception as e:
                logger.error("Unable to download image '%s', skipping."
                              % image)
                print e
