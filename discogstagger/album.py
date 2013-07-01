import logging
import re

import discogs_client as discogs

logger = logging.getLogger(__name__)

class BaseObject(object):

    pass

class Track(BaseObject):
    """ A disc contains several tracks, each track has a tracknumber,
        a title, an artist """

    def __init__(self, tracknumber, title, artists):
        self.tracknumber = tracknumber
        self.title = title
        self.artists = artists

class Disc(BaseObject):
    """ An album has one or more discs, each disc has a number and
        could have also a disctitle, furthermore several tracks
        are on each disc """

    def __init__(self, discnumber):
        self.discnumber = discnumber
        self.tracks = []

class Album(BaseObject):
    """ An album contains one or more discs and has a title, an artist
        (special case: Various), a source identifier (eg. discogs_id)
        and a catno """

    def __init__(self, identifier, title, artists):
        self.id = identifier
        self.artists = artists
        self.title = title
        self.discs = []
        self.fileformat = "flac"
