import logging
import re
import os

import inspect

import time

import discogs_client as discogs

from rauth import OAuth1Service

from album import Album, Disc, Track

logger = logging.getLogger(__name__)

class RateLimit(object):
    pass

class DiscogsConnector(object):
    """ central class to connect to the discogs api server.
        this should be a singleton, to allow the usage of authentication and rate-limiting
        encapsules all discogs information retrieval
    """

    def __init__(self, tagger_config):
        self.config = tagger_config
        discogs.user_agent = self.config.get("common", "user_agent")

        self.discogs_auth = None
        self.discogs_session = None
        self.rate_limit_pool = {}

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
        if os.environ.has_key("DISCOGS_CONSUMER_KEY"):
            consumer_key = os.environ.get('DISCOGS_CONSUMER_KEY')
        if os.environ.has_key("DISCOGS_CONSUMER_SECRET"):
            consumer_secret = os.environ.get("DISCOGS_CONSUMER_SECRET")

        if consumer_key and consumer_secret:
            logger.debug('authenticating at discogs using consumer key %s' % consumer_key)

            self.discogs_auth = OAuth1Service(
                consumer_key=consumer_key,
                consumer_secret=consumer_secret,
                name="discogs",
                access_token_url='http://api.discogs.com/oauth/access_token',
                authorize_url='http://www.discogs.com/oauth/authorize',
                request_token_url='http://api.discogs.com/oauth/request_token',
                base_url='http://api.discogs.com'
            )
        else:
            logger.warn('cannot authenticate on discogs (no image download possible) - set consumer_key and consumer_secret')

    def fetch_release(self, release_id):
        """ fetches the metadata for the given release_id from the discogs api server
            (no authentication necessary, specific rate-limit implemented on this one)
        """
        rate_limit_type = 'metadata'

        if rate_limit_type in self.rate_limit_pool:
            if self.rate_limit_pool[rate_limit_type].lastcall >= time.time() - 1:
                logger.warn('Waiting one second to allow rate limiting...')
                time.sleep(1)

        rl = RateLimit()
        rl.lastcall = time.time()

        self.rate_limit_pool[rate_limit_type] = rl

        return discogs.Release(release_id)

    def authenticate(self):
        """ Authenticates the user on the discogs api via oauth 1.0a
            Since we are running a command line application, a prompt will ask the user for a
            request_token_secret (pin), which the user can get from the authorize_url, which
            needs to get called manually.
        """
        if self.discogs_auth and not self.discogs_session:
            logger.debug('discogs authenticated')
            logger.debug('no request_token and request_token_secret, fetch them')
            request_token, request_token_secret = self.discogs_auth.get_request_token()

            authorize_url = self.discogs_auth.get_authorize_url(request_token)

            print 'Visit this URL in your browser: ' + authorize_url
            pin = raw_input('Enter the PIN you got from the above url: ')

            self.discogs_session = self.discogs_auth.get_auth_session(request_token, request_token_secret,
                                                                      method='GET', data={'oauth_verifier': pin})

            logger.debug('filled session....')

    def fetch_image(self, image_dir, image_url):
        """
            There is a need for authentication here, therefor before every call the authenticate method will
            be called, to make sure, that the user is authenticated already. Furthermore, discogs restricts the
            download of images to 1000 per day. This can be very low on huge volume collections ;-(
        """
        rate_limit_type = 'image'

        if not self.discogs_session:
            logger.error('You are not authenticated, cannot download image - skipping')
            return

        if rate_limit_type in self.rate_limit_pool:
            remaining = self.rate_limit_pool[rate_limit_type].remaining
            reset = self.rate_limit_pool[rate_limit_type].reset
            logger.debug('You have %s remaining downloads for the next %s seconds' % (remaining, reset))
            if remaining <= 1:
                logger.error('Your download limit is reached, you cannot download the wanted picture today')
                logger.error('Download can be started again in %d seconds' % self.rate_limit_pool[rate_limit_type].reset)
                raise RuntimeError('Download limit reached for pool %s' % rate_limit_type)


        try:
            r = self.discogs_session.get(image_url, stream=True)
            if r.status_code == 200:
                with open(image_dir, 'wb') as f:
                    for chunk in r.iter_content():
                        f.write(chunk)
            else:
                logger.error('Problem downloading (status code %s)' % r.status_code)

            self.updateRateLimits(r)
        except Exception as e:
            logger.error("Unable to download image '%s', skipping." % image_url)
            print e


    def updateRateLimits(self, request):
        type = request.headers['X-RateLimit-Type']

        rl = RateLimit()
        rl.limit = request.headers['X-RateLimit-Limit']
        rl.remaining = request.headers['X-RateLimit-Remaining']
        rl.reset = request.headers['X-RateLimit-Reset']

        self.rate_limit_pool[type] = rl


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

    def __init__(self, releaseid, tagger_config):
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
        album.country = self.release.data["country"]
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

        return "http://www.discogs.com/release/{}".format(self.release._id)

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
        """ Obtain the number of discs for the given release. """

        # allows tagging of digital releases.
        # sample format <format name="File" qty="2" text="320 kbps">
        # assumes all releases of name=File is 1 disc.
        if self.release.data["formats"][0]["name"] == "File":
            return 1

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
        last_artist = None

        for x in artist_data:
            if isinstance(x, basestring):
                last_artist = last_artist + " " + x
            else:
                if not last_artist == None:
                    last_artist = last_artist + " " + self.clean_name(x.name)
                    artists.append(last_artist)
                    last_artist = None
                else:
                    last_artist = self.clean_name(x.name)

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
