#!/bin/sh
python2 scripts/fetch_json.py -r $1 -c conf/discogs_tagger_triplem_new.conf 
mv $1.json $2/$1.json
