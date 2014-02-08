#!/bin/sh
#
# discogs_client needs the deprecated endpoint (/release/ instead of /releases/)
#
wget --header='Content-Type: application/json' http://api.discogs.com/release/$1 -O $1.json
