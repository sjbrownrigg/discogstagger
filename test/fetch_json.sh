#!/bin/sh
#
# discogs_client needs the deprecated endpoint (/release/ instead of /releases/)
#
wget --header='Content-Type: application/json' http://api.discogs.com/releases/$1 -O $1.json
