#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
from io import StringIO

import json

from discogstagger.discogsalbum import DiscogsAlbum, DummyResponse, LocalDiscogsConnector, DiscogsConnector
import discogs_client as discogs

class TestDummyResponse(DummyResponse):
    def __init__(self, releaseid):
        __location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

        path = os.path.join(__location__, "release")
        DummyResponse.__init__(self, releaseid, path)

class DummyDiscogsAlbum(DiscogsAlbum):
    def __init__(self, dummy_response):
        # we need a dummy client here ;-(
        client = discogs.Client('Dummy Client - just for unit testing')

        self.dummy_response = dummy_response
        self.content = self.convert(json.loads(dummy_response.content))

        self.release = discogs.Release(client, self.content['resp']['release'])

        DiscogsAlbum.__init__(self, self.release)

    def convert(self, input):
        if isinstance(input, dict):
            return {self.convert(key): self.convert(value) for key, value in input.iteritems()}
        elif isinstance(input, list):
            return [self.convert(element) for element in input]
        elif isinstance(input, unicode):
            return input.encode('utf-8')
        else:
            return input


