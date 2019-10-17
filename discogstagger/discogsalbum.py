import logging
import re
import os
import urllib
import urllib.request
import string

import pprint
pp = pprint.PrettyPrinter(indent=4)
from ext.mediafile import MediaFile

from datetime import time as Time
from datetime import timedelta, datetime
import time

import discogs_client as discogs

import json

from discogstagger.album import Album, Disc, Track

logger = logging

class DiscogsSearch(object):
    """ Search for a release based on the existing
        metadata of the files in the source directory
    """
    def __init__(self, tagger_config):
        self.config = tagger_config
        self.cue_done_dir = '.cue'

    def getSearchParams(self, source_dir):
        """ get search parameters to find release on discogs
        """

        print('Setting original metadata for search purposes')

        files = self._getMusicFiles(source_dir)

        searchParams = {}
        for file in files:

            head, tail = os.path.split(file)

            file = tail

            print(file)
            metadata = MediaFile(os.path.join(source_dir, file))

            searchParams['artist'] = metadata.artist
            searchParams['albumartist'] = metadata.albumartist
            searchParams['album'] = metadata.album
            searchParams['year'] = metadata.year
            searchParams['date'] = metadata.date
            searchParams['disc'] = metadata.disc
            if 'tracks' not in searchParams:
                searchParams['tracks'] = {}
            track = str(metadata.disc) + '-' + str(metadata.track) if metadata.disc else str(metadata.track)
            if track not in searchParams['tracks']:
                searchParams['tracks'][track] = {}
            searchParams['tracks'][track]['duration'] = str(timedelta(seconds = round(metadata.length, 0)))
            searchParams['tracks'][track]['title'] = metadata.title
            searchParams['tracks'][track]['artist'] = metadata.artist # useful for compilations
        print(searchParams)

        return searchParams

    def _getMusicFiles(self, source_dir):
        """ Get album data
        """
        extf = (self.cue_done_dir)
        found = []
        for root,dirs,files in os.walk(source_dir):
            dirs[:] = [d for d in dirs if d not in extf]
            for file in files:
                if file.endswith(('.flac', '.mp3')):
                    found.append(os.path.join(root, file))
        return found

class AlbumError(Exception):
    """ A central exception for all errors happening during the album handling
    """
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)

class RateLimit(object):
    pass

class DiscogsConnector(object):
    """ central class to connect to the discogs api server.
        this should be a singleton, to allow the usage of authentication and rate-limiting
        encapsules all discogs information retrieval
    """

    def __init__(self, tagger_config):
        self.config = tagger_config
        self.user_agent = self.config.get("common", "user_agent")
        self.discogs_client = discogs.Client(self.user_agent)
        self.tracklength_tolerance = self.config.getfloat("batch", "tracklength_tolerance")
        self.discogs_auth = False
        self.rate_limit_pool = {}
        self.release_cache = {}

        skip_auth = self.config.get("discogs", "skip_auth")

        if skip_auth != "True":
            self.initialize_auth()
            self.authenticate()

    def initialize_auth(self):
        """ initializes the authentication against the discogs api
            this method checks for the consumer_key and consumer_secret in the config
            and then in the environment variables, to allow overriding these values on the
            command line
        """
        # allow authentication to be able to download images (use key and secret from config options)
        consumer_key = self.config.get("discogs", "consumer_key")
        consumer_secret = self.config.get("discogs", "consumer_secret")

        # allow config override thru env variables
        if 'DISCOGS_CONSUMER_KEY' in os.environ:
            consumer_key = os.environ.get('DISCOGS_CONSUMER_KEY')
        if 'DISCOGS_CONSUMER_SECRET' in os.environ:
            consumer_secret = os.environ.get('DISCOGS_CONSUMER_SECRET')

        if consumer_key and consumer_secret:
            logger.debug('authenticating at discogs using consumer key {0}'.format(consumer_key))

            self.discogs_client.set_consumer_key(consumer_key, consumer_secret)
            self.discogs_auth = True
        else:
            logger.warn('cannot authenticate on discogs (no image download possible) - set consumer_key and consumer_secret')

    def fetch_release(self, release_id, source_dir):
        return self.fetch_release(release_id)

    def fetch_release(self, release_id):
        """ fetches the metadata for the given release_id from the discogs api server
            (authentication necessary as well, specific rate-limit implemented on this one)
        """
        logger.info("fetching release with id %s" % release_id)

        if not self.discogs_auth:
            logger.error('You are not authenticated, cannot download image metadata')

        rate_limit_type = 'metadata'

        if rate_limit_type in self.rate_limit_pool:
            if self.rate_limit_pool[rate_limit_type].lastcall >= time.time() - 5:
                logger.warn('Waiting one second to allow rate limiting...')
                time.sleep(5)

        rl = RateLimit()
        rl.lastcall = time.time()

        self.rate_limit_pool[rate_limit_type] = rl

        return self.discogs_client.release(int(release_id))

    def authenticate(self):
        """ Authenticates the user on the discogs api via oauth 1.0a
            Since we are running a command line application, a prompt will ask the user for a
            request_token_secret (pin), which the user can get from the authorize_url, which
            needs to get called manually.
        """
        if self.discogs_auth:
            access_token, access_secret = self.read_token()

            if not access_token or not access_secret:
                logger.debug('no request_token and request_token_secret, fetch them')
                request_token, request_token_secret, authorize_url = self.discogs_client.get_authorize_url()

                print('Visit this URL in your browser: ' + authorize_url)
                pin = input('Enter the PIN you got from the above url: ')

                access_token, access_secret = self.discogs_client.get_access_token(pin)

                token_file = self.construct_token_file()
                with open(token_file, 'w') as fh:
                    fh.write('{0},{1}'.format(access_token, access_secret))
            else:
                self.discogs_client.set_token(str(access_token), str(access_secret))

            logger.debug('filled session....')

    def read_token(self):
        """
            Reads the token-file and returns the contained access_token and access_secret, if available
        """
        token_file = self.construct_token_file()

        access_token = None
        access_secret = None

        try:
            if os.path.join(token_file):
                with open(token_file, 'r') as tf:
                    access_token, access_secret = tf.read().split(',')
        except IOError:
            pass

        return access_token, access_secret


    def construct_token_file(self):
        """
            Constructs the file in which the token is stored
        """
        cwd = os.getcwd()
        token_file_name = '.token'
        return os.path.join(cwd, token_file_name)


    def _rateLimit(self):
        rate_limit_type = 'metadata'

        if rate_limit_type in self.rate_limit_pool:
            if self.rate_limit_pool[rate_limit_type].lastcall >= time.time() - 1:
                logger.warn('Waiting one second to allow rate limiting...')
                time.sleep(1)

        rl = RateLimit()
        rl.lastcall = time.time()

        self.rate_limit_pool[rate_limit_type] = rl

    def search_artist_title(self, searchParams, candidates):
        self._rateLimit()

        album = searchParams['album']
        artist = ''
        if searchParams['albumartist'] is not None and searchParams['albumartist'].lower() in ('various', 'various artists', 'va'):
            artist = searchParams['tracks'][0]['artist'] # take the first artist from the compiltaion
        else:
            artist = searchParams['artist']

        artistTitleSearch = ' '.join((artist, album))

        print('Searching by artist and title: {}'.format(artistTitleSearch))
        results = self.discogs_client.search(artistTitleSearch, type='all')

        print(results)

        for idx, result in enumerate(results):
            # print('Search: {}; index: {}'.format(artistTitleSearch, idx))
            # print(dir(result))
            # print(dir(result.data))
            # if hasattr(result, 'master'):
            #     print(result.master)
            #     print(result.id)
            #     exit()
            if hasattr(result, 'versions'):
                print(result.versions)
                self._siftReleases(searchParams, result.versions, candidates)

        # return candidates


    def search_artist(self, searchParams, candidates):
        self._rateLimit()

        album = searchParams['album']
        artist = ''
        if searchParams['albumartist'] is not None and searchParams['albumartist'].lower() in ('various', 'various artists', 'va'):
            artist = searchParams['tracks'][0]['artist'] # take the first artist from the compiltaion
        else:
            artist = searchParams['artist']

        # reuse release data for this artist previously cached in this session
        if artist in self.release_cache:
            releases = self.release_cache[artist]
            print('reusing cached artist data')
        else:
            results = self.discogs_client.search(artist, type='artist')
            for result in results:
                if len(candidates) > 0: # stop if we have found some candidates
                    continue

                found = []
                a = artist.lower()
                # workaround for many artists with the same name, e.g. Deimos (3)
                n = re.sub('\s+\(\d+\)$', '', result.name.lower()).strip()
                if a == n:
                # session based cache to reuse artist release data
                    self.release_cache['artist'] = result.releases
                    releases = result.releases

        for release in result.releases:
            if len(candidates) > 0:
                continue

            self._rateLimit()
            r = release.title.lower()
            s = searchParams['album'].lower()
            if s == r or r in s or s in r: # sometimes titles include extra info, e.g. EP
                found.append('title')
                pp.pprint('matched title')
                pp.pprint(release.title)
                print()
                if not hasattr(release, 'versions'):
                    if self._compareRelease(searchParams, release) == True:
                        candidates[release.id] = release
                else:
                    self._siftReleases(searchParams, release.versions, candidates)

        # return candidates


    def search_discogs(self, searchParams):
        self._rateLimit()

        print('Searching discogs')

        candidates = {}

        self.search_artist_title(searchParams, candidates)

        print('has searched for artist and title')
        print(candidates)

        if len(candidates) == 0:
            self.search_artist(searchParams, candidates)

        print(candidates)

        if len(candidates) == 1:
            return list(candidates.values())[0]

# TODO: find a better way of sifting through multiple positive matches
        elif len(candidates) > 1:
            return list(candidates.values())[0]
            if searchParams['year'] is not None:
                for version in candidates:
                    print(version.id)
                    if searchParams['year'] == version.year:
                        return version.id
            elif version.format == 'CD':
                        return version.id
        else:
            return None


    def _siftReleases(self, searchParams, releases, candidates):
        # if we have a year, start by limiting the releases we sift
        if 'year' in searchParams and searchParams['year'] is not None:
            for release in releases:
                if release.id in candidates.keys():
                    continue

                self._rateLimit()
                if searchParams['year'] == release.year:
                    print('got a year match')
                    pp.pprint(release.id)
                    pp.pprint(searchParams['year'])
                    pp.pprint(release.year)
                    if self._compareRelease(searchParams, release) == True:
                        candidates[release.id] = release
                elif release.year is None or release.year == '':
                    continue
                elif release.year > searchParams['year']:
                    break
        # if no match by limiting on date, or there is no date ...
        if len(candidates) == 0:
            print('no candidates, trying without date limits')
            for release in releases:
                self._rateLimit()
                pp.pprint(release.id)
                pp.pprint(release.year)
                if self._compareRelease(searchParams, release) == True:
                    candidates[release.id] = release
        # return candidates

    def _compareRelease(self, searchParams, release):
        self._rateLimit()
        trackInfo = self._getTrackInfo(release)
        pp.pprint(trackInfo)
        pp.pprint(searchParams)
        if len(searchParams['tracks']) == len(trackInfo):
            if self._compareTracks(searchParams, trackInfo) < self.tracklength_tolerance:
                logger.debug('adding relid to the list of candidates: {}'.format(release.id))
                return True
        else:
            return False


    def _paddedHMS(self, string):
        array = [int(s) for s in string.split(':')]
        while len(array) < 3:
            array.insert(0, 0)
        narray = ['{:0>2}'.format(d) for d in array ]
        return ':'.join(narray)

    def _compareTracks(self, current, imported):
        """ Compare original tracklist against discogs tracklist, by comparing
            the track lengths. Some releases have tracks in different order,
            so we need to weed those out.  Returns the highest value.
        """
        tolerance = 0.0
        curr_tracklist = current['tracks']
        for track in curr_tracklist.keys():
            """ some tracks have alphanumerical identifiers,
                e.g. vinyl, cassettes
            """
            if track not in imported.keys():
                logging.debug('track not present, numbering format different')
                return 100
            else:
                try:
                    a = self._paddedHMS(curr_tracklist[track]['duration'])
                    b = self._paddedHMS(imported[track]['duration'])
                    timea = datetime.strptime(a, '%H:%M:%S')
                    timeb = datetime.strptime(b, '%H:%M:%S')
                    difference = timea - timeb
                    if difference.total_seconds() > tolerance:
                        tolerance = difference.total_seconds()
                except Exception as e:
                    print(e)
            logging.debug('tracklength tolerance for release (change if there are any matching issues):  {}'.format(tolerance))
        return tolerance

    def _getTrackInfo(self, version):
        """ Get the track values from the release, so that we can compare them
            to what we have got.  Remove extra info appearing with empty track
            number, e.g. Bonus tracks, or section titles.
        """
        self._rateLimit()
        trackinfo = {}
        for track in version.tracklist:
            if str(track.position) == '':
                logger.debug('ignoring non-track info: {}'.format(getattr(track, 'title')))
                continue
            pos = str(track.position)
            trackinfo[pos] = {}
            for key in ['duration', 'title']:
                trackinfo[pos][key] = getattr(track, key)
        return trackinfo

    def fetch_image(self, image_dir, image_url):
        """
            There is a need for authentication here, therefor before every call the authenticate method will
            be called, to make sure, that the user is authenticated already. Furthermore, discogs restricts the
            download of images to 1000 per day. This can be very low on huge volume collections ;-(
        """
        rate_limit_type = 'image'

        if not self.discogs_auth:
            logger.error('You are not authenticated, cannot download image - skipping')
            return

        if rate_limit_type in self.rate_limit_pool:
            if self.rate_limit_pool[rate_limit_type].lastcall >= time.time() - 5:
                logger.warn('Waiting one second to allow rate limiting...')
                time.sleep(5)

        rl = RateLimit()
        rl.lastcall = time.time()

        try:
            urllib.request.urlretrieve(image_url,  image_dir)
            # urllib.urlretrieve(image_url,  image_dir)

            self.rate_limit_pool[rate_limit_type] = rl
        except Exception as e:
            logger.error("Unable to download image '%s', skipping. (%s)" % (image_url, e))

class DummyResponse(object):
    """
        The dummy response used to create a discogs.release from a local json file
    """
    def __init__(self, release_id, json_path):
        self.releaseid = release_id

        json_file_name = "%s.json" % self.releaseid
        json_file_path = os.path.join(json_path, json_file_name)

        json_file = open(json_file_path, "r")

        self.status_code = 200
        self.content = json_file.read()

class LocalDiscogsConnector(object):
    """ use local json, do not fetch json from discogs, instead use the one in the source_directory
        We will need to use the Original DiscogsConnector to allow the usage of the authentication
        for fetching images.
    """

    def __init__(self, delegate_discogs_connector):
        self.delegate = delegate_discogs_connector

    def fetch_release(self, release_id):
        pass

    def fetch_release(self, release_id, source_dir):
        """ fetches the metadata for the given release_id from a local file
        """
        dummy_response = DummyResponse(release_id, source_dir)

        # we need a dummy client here ;-(
        client = discogs.Client('Dummy Client - just for testing')

        self.content = self.convert(json.loads(dummy_response.content))

        logger.debug('content: %s' % self.content)

        release = discogs.Release(client, self.content)

        return release

    def authenticate(self):
        self.delegate.authenticate()

    def fetch_image(self, image_dir, image_url):
        self.delegate.fetch_image(image_dir, image_url)

    def updateRateLimits(self, request):
        self.delegate.updateRateLimits(request)

    def convert(self, input):
        """ This is an exact copy of a method in _common_test, please refactor
        """
        if isinstance(input, dict):
            return {self.convert(key): self.convert(value) for key, value in input.iteritems()}
        elif isinstance(input, list):
            return [self.convert(element) for element in input]
        # elif isinstance(input, unicode):
        #     return input.encode('utf-8')
        else:
            return input


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

    def __init__(self, release):
        self.release = release

    def map(self):
        """ map the retrieved information to the tagger specific objects """

        album = Album(self.release.id, self.release.title, self.album_artists(self.release.artists))

        album.sort_artist = self.sort_artist(self.release.artists)
        album.url = self.url
        album.catnumbers = [catno for name, catno in self.labels_and_numbers]
        album.labels = [name for name, catno in self.labels_and_numbers]
        album.images = self.images
        album.year = self.year
        album.format = self.release.data["formats"][0]["name"]
        album.genres = self.release.data["genres"]

        try:
            album.styles = self.release.data["styles"]
        except KeyError:
            album.styles = [""]

        if "country" in self.release.data:
            album.country = self.release.data["country"]
        else:
            logging.warn("no country set for relid %s" % self.release.id)
            album.country = ""

        if "notes" in self.release.data:
            album.notes = self.release.data["notes"]

        album.disctotal = self.disctotal
        album.is_compilation = self.is_compilation

        album.master_id = self.master_id

        album.discs = self.discs_and_tracks(album)

        return album

    @property
    def url(self):
        """ returns the discogs url of this release """

        return "http://www.discogs.com/release/{}".format(self.release.id)

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
        except AttributeError:
            return "1900"

    @property
    def disctotal(self):
        """ Obtain the number of discs for the given release. """

        discno = 0

        # allows tagging of digital releases.
        # sample format <format name="File" qty="2" text="320 kbps">
        # assumes all releases of name=File is 1 disc.
        if self.release.data["formats"][0]["name"] == "File":
            discno = 1
        else:
            discno = int(self.release.data["formats"][0]["qty"])

        logger.info("determined %d no of discs total" % discno)
        return discno

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
            # an artist object.
            # AttributeError: 'unicode' object has no attribute 'name'
            # [<Artist "A.D.N.Y*">, u'Presents', <Artist "Leiva">]
            try:
                yield x.name
            except AttributeError:
                pass

    def album_artists(self, artist_data):
        """ obtain the artists (normalized using clean_name).
            the handling of the 'join' stuff is not implemented in discogs_client ;-(
        """
        artists = []

        last_artist = None
        for x in artist_data:
            logger.debug("album-x: %s" % x.name)
            artists.append(self.clean_name(x.name))

        return artists

    def artists(self, artist_data):
        """ obtain the artists (normalized using clean_name). this is specific for tracks, since tracks are handled
            differently from the album artists.
            here the "join" is taken into account as well....

        """
        artists = []
        last_artist = None
        join = None

        for x in artist_data:
#            logger.debug("x: %s" % vars(x))
#            logger.debug("join: %s" % x.data['join'])

            if isinstance(x, str):
                logger.debug("x: %s" % x)
                if last_artist:
                    last_artist = last_artist + " " + x
                else:
                    last_artist = x
            else:
                if not last_artist == None:
                    logger.debug("name: %s" % x.name)
                    concatString = " "
                    if not join == None:
                        concatString = " " + join + " "

                    last_artist = last_artist + concatString + self.clean_name(x.name)
                    artists.append(last_artist)
                    last_artist = None
                else:
                    join = x.data['join']
                    last_artist = self.clean_name(x.name)

            logger.debug("last_artist: %s" % last_artist)

        artists.append(last_artist)

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
                "^(?P<discnumber>\d+).(?P<tracknumber>\d+)$",   # 1.05 (this is not multi-disc but multi-tracks for one track)....
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

            if t.position is None:
                logging.error("position is null, shouldn't be...")

            if t.position.startswith("Video") or t.position.startswith("video") or t.position.startswith("DVD"):
                continue

            # on multiple discs there do appears a subtitle as the first "track"
            # on the cd in discogs, this seems to be wrong, but we would like to
            # handle it anyway
            if t.title and not t.position and not t.duration:
                discsubtitle = t.title
                continue

            # this seems to be an index track, set the discsubtitle
            if hasattr(t, 'type_') and t.type_ != "Track":
                # we are not storing the subtitle on the disc, since it can happen,
                # that the discsubtitleis just for the following tracks
                discsubtitle = t["title"]
                continue

            if t.artists:
                artists = self.artists(t.artists)
                sort_artist = self.sort_artist(t.artists)
            else:
                artists = album.artists
                sort_artist = album.sort_artist

            track = Track(i + 1, t.title, artists)

            track.position = i

            pos = self.disc_and_track_no(t.position)
            try:
                track.tracknumber = int(pos["tracknumber"])
                track.discnumber = int(pos["discnumber"])
            except ValueError as ve:
                msg = "cannot convert {0} to a valid track-/discnumber".format(t.position)
                logger.error(msg)
                raise AlbumError(msg)

#            logger.debug("discsubtitle: {0}".format(discsubtitle))
            if discsubtitle:
                track.discsubtitle = discsubtitle

            track.sort_artist = sort_artist

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
            ("(.*),\sThe$", "The \g<1>"),
        }

        clean_target = self.clean_duplicate_handling(clean_target)

        for regex in groups:
            clean_target = re.sub(regex[0], regex[1], clean_target)

        return clean_target
