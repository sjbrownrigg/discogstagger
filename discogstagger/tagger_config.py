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

        self.config.read(config_file)

    @property
    def id_tag_name(self):
        source_name = self.config.get("source", "name")
        id_tag_name = self.config.get("source", source_name)

        return id_tag_name

    def get_without_quotation(self, section, name):
        config_value = self.config.get(section, name)
        return config_value.replace("\"", "")

    def get(self, section, name):
        config_value = self.config.get(section, name)

        if config_value == "":
          config_value = None

        return config_value

    def getboolean(self, section, name):
        return self.config.getboolean(section, name)

    def add_config(self, config_file):
        self.config.read(config_file)
