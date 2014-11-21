import os, errno, sys

import shutil
import fileinput

import logging

from optparse import OptionParser

from ConfigParser import SafeConfigParser

logging.basicConfig(level=10)
logger = logging.getLogger(__name__)

def find_files(basepath, name):
    result = []

    logging.debug('id recognition starts in %s for files %s' % (basepath, name))

    base = os.path.expanduser(basepath)

    for root, dirs, files in os.walk(base):
        if name in files:
            result.append(os.path.join(root, name))
            logger.debug("added file: %s" % name)

    return result

p = OptionParser()
p.add_option("-b", "--basedir", action="store", dest="basedir",
             help="The (base) directory to search for id files to migrate")
(options, args) = p.parse_args()

logging.debug('starting id finder')
files = find_files(options.basedir, "id.txt")

logging.debug('find ids in %d files' % len(files))

id_list = []
target_file = open('local_ids.txt', 'w')


parser = SafeConfigParser()

for filename in files:
    parser.read(filename)
    logging.debug("%s has value %s" % (filename, parser.get('source', 'discogs_id')))
    target_file.write("%s\n" % parser.get('source', 'discogs_id'))
