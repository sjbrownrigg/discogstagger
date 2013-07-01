import os
import logging

import inspect

import ConfigParser
from optparse import OptionParser

logger = logging.getLogger(__name__)

class TaggerConfig(object):
		""" provides the configuration mechanisms for the discogstagger """
		def __init__(self, config_file):
				self.config = ConfigParser.ConfigParser()
				self.config.read(os.path.join("conf", "default.conf"))

#				logger.debug("config: %s " % inspect.getmembers(self.config))

				self.config.read(config_file)	
