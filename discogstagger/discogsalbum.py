import logging
import re

import inspect

import discogs_client as discogs

from album import Album, Disc, Track

class memoized_property(object):

    def __init__(self, fget, doc=None):
        self.fget = fget
        self.__doc__ = doc or fget.__doc__
        self.__name__ = fget.__name__

    def __get__(self, obj, cls):
        if obj is None:
            return self
        obj.__dict__[self.__name__] = result = self.fget(obj)
        return result

logger = logging.getLogger(__name__)

class DiscogsAlbum(object):
    """ Wraps the discogs-client-api script, abstracting the minimal set of
        artist data required to tag an album/release

        >>> from discogstagger.discogsalbum import DiscogsAlbum
        >>> release = DiscogsAlbum(40522) # fetch discogs release id 40522
        >>> print "%s - %s (%s / %s)" % (release.artist, release.title, release.catno,
        >>> release.label)

        Blunted Dummies - House For All (12DEF006 / Definitive Recordings)

        >>> for song in release.tracks: print "[ %.2d ] %s - %s" % (song.position,
        >>> song.artist, song.title)

        [ 01 ] Blunted Dummies - House For All (Original Mix)
        [ 02 ] Blunted Dummies - House For All (House 4 All Robots Mix)
        [ 03 ] Blunted Dummies - House For All (Eddie Richard's Mix)
        [ 04 ] Blunted Dummies - House For All (J. Acquaviva's Mix)
        [ 05 ] Blunted Dummies - House For All (Ruby Fruit Jungle Mix) """

    def __init__(self, releaseid):
        discogs.user_agent = "discogstagger +http://github.com/jesseward"
        self.release = discogs.Release(releaseid)

    def map(self):
        """ map the retrieved information to the tagger specific objects """

        album = Album(self.release._id, self.release.title, self.artists(self.release.artists))

        album.sort_artist = self.sort_artist(self.release.artists)
        album.url = self.url
        album.catnumbers = [catno for name, catno in self.labels_and_numbers]
        album.labels = [name for name, catno in self.labels_and_numbers]
        album.images = self.images
        album.year = self.year
        album.genres = self.release.data["genres"]
        album.styles = self.release.data["styles"]
        album.year = self.release.data["country"]
        if "notes" in self.release.data:
            album.notes = self.release.data["notes"]
        album.disctotal = self.disctotal
        album.is_compilation = self.is_compilation

        album.discs = self.discs_and_tracks(album)

        return album

## should be refactored to taggerutils or somewhere, use a template based approach then
    @property
    def album_info(self):
        """ Dumps the release data to a formatted text string. Formatted for
            .nfo file  """

        logger.debug("Writing nfo file")
        div = "_ _______________________________________________ _ _\n"
        r = div
        r += "  Name : %s - %s\n" % (self.artist, self.title)
        r += " Label : %s\n" % (self.label)
        r += " Genre : %s\n" % (self.genre)
        r += " Catno : %s\n" % (self.catno)
        r += "  Year : %s\n" % (self.year)
        r += "   URL : %s\n" % (self.url)

        if self.master_id:
            r += "Master : http://www.discogs.com/master/%s\n" % self.master_id

        r += div
        for song in self.tracks:
            r += "%.2d. %s - %s\n" % (song.position, song.artist, song.title)
        return r

    @property
    def url(self):
        """ returns the discogs url of this release """

        return "http://www.discogs.com/release/%s" % self.release._id

    @property
    def labels_and_numbers(self):
        """ Returns all available catalog numbers"""
        for label in self.release.data["labels"]:
            yield self.clean_duplicate_handling(label["name"]), label["catno"]

    @property
    def images(self):
        """ return a single list of images for the given album """

        try:
            return [x["uri"] for x in self.release.data["images"]]
        except KeyError:
            pass

    @property
    def year(self):
        """ returns the album release year obtained from API 2.0 """

        good_year = re.compile("\d\d\d\d")
        try:
            return good_year.match(str(self.release.data["year"])).group(0)
        except IndexError:
            return "1900"

    @property
    def disctotal(self):
        return int(self.release.data["formats"][0]["qty"])

    @property
    def master_id(self):
        """ returns the master release id """

        try:
            return self.release.data["master_id"]
        except KeyError:
            return None

    def _gen_artist(self, artist_data):
        """ yields a list of artists name properties """
        for x in artist_data:
            # bugfix to avoid the following scenario, or ensure we're yielding
            # and artist object.
            # AttributeError: 'unicode' object has no attribute 'name'
            # [<Artist "A.D.N.Y*">, u'Presents', <Artist "Leiva">]
            try:
                yield x.name
            except AttributeError:
                pass

    def artists(self, artist_data):
        """ obtain the artists (normalized using clean_name). """
        artists = []
        for x in artist_data:
# !TODO
            if isinstance(x, basestring):
                logger.debug("artist is string (join) - need to implement: %s " % x)
# append the previous artist with the next one
# can we just easily join the whole list?????
            else:
                artists.append(self.clean_name(x.name))


        return artists

    def sort_artist(self, artist_data):
        """ Obtain a clean sort artist """
        return self.clean_duplicate_handling(artist_data[0].name)

    def disc_and_track_no(self, position):
        """ obtain the disc and tracknumber from given position
            problem right now, discogs uses - and/or . as a separator, furthermore discogs uses
            A1 for vinyl based releases, we should implement this as well
        """
        if position.find("-") > -1 or position.find(".") > -1:
            # some variance in how discogs releases spanning multiple discs
            # or formats are kept, add regexs here as failures are encountered
            NUMBERING_SCHEMES = (
                "^CD(?P<discnumber>\d+)-(?P<tracknumber>\d+)$", # CD01-12
                "^(?P<discnumber>\d+)-(?P<tracknumber>\d+)$",   # 1-02
                "^(?P<discnumber>\d+).(?P<tracknumber>\d+)$",   # 1.05
            )

            for scheme in NUMBERING_SCHEMES:
                re_match = re.search(scheme, position)

                if re_match:
                    return {'tracknumber': re_match.group("tracknumber"),
                            'discnumber': re_match.group("discnumber")}
        else:
            return {'tracknumber': position,
                    'discnumber': 1}


        logging.error("Unable to match multi-disc track/position")
        return False

    def tracktotal_on_disc(self, discnumber):
        logger.debug("discs: %s" % self.discs)
        return self.discs[discnumber]

    @property
    def is_compilation(self):
        if self.release.data["artists"][0]["name"] == "Various":
            return True

        for format in self.release.data["formats"]:
            if "descriptions" in format:
                for description in format["descriptions"]:
                    if description == "Compilation":
                        return True

        return False

    def discs_and_tracks(self, album):
        """ provides the tracklist of the given release id """

        disc_list = []
        track_list = []
        discsubtitle = None
        disc = Disc(1)

        discsubtitle = None

        for i, t in enumerate(x for x in self.release.tracklist):

            # this seems to be an index track, set the discsubtitle
            if t["type"] != "Track":
                # we are not storing the subtitle on the disc, since it can happen,
                # that the discsubtitleis just for the following tracks
                discsubtitle = t["title"]
                continue

            if t["artists"]:
                artists = self.artists(t["artists"])
                sort_artist = self.sort_artist(t["artists"])
            else:
                artists = album.artists
                sort_artist = album.sort_artist

            track = Track(i + 1, t["title"], artists)

            track.position = i

            pos = self.disc_and_track_no(t["position"])
            track.tracknumber = int(pos["tracknumber"])
            track.discnumber = int(pos["discnumber"])

#            logger.debug("discsubtitle: %s " % discsubtitle)
            if discsubtitle:
                track.discsubtitle = discsubtitle

            track.sortartists = sort_artist

            if track.discnumber != disc.discnumber:
                disc_list.append(disc)
                disc = Disc(track.discnumber)

            disc.tracks.append(track)

        disc_list.append(disc)
        return disc_list

    def clean_duplicate_handling(self, clean_target):
        """ remove discogs duplicate handling eg : John (1) """
        return re.sub("\s\(\d+\)", "", clean_target)

    def clean_name(self, clean_target):
        """ Cleans up the format of the artist or label name provided by
            Discogs.
            Examples:
                'Goldie (12)' becomes 'Goldie'
                  or
                'Aphex Twin, The' becomes 'The Aphex Twin'
            Accepts a string to clean, returns a cleansed version """

        groups = {
            "(.*),\sThe$": "The",
        }

        clean_target = self.clean_duplicate_handling(clean_target)

        for regex in groups:
            if re.search(r"%s" % regex, clean_target):
                clean_target = "%s %s" % (groups[regex],
                                          re.search("%s" % regex,
                                          clean_target).group(1))
        return clean_target
