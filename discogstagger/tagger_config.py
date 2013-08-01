import os
import logging

import inspect

import ConfigParser
from optparse import OptionParser

logger = logging.getLogger(__name__)

# !TODO This could be made slightly easier by extending the original ConfigParser
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

# !TODO cache the following, to not recreate it on every call
    @property
    def get_character_exceptions(self):
        """ placeholders for special characters within character exceptions. """

        exceptions = self.config._sections["character_exceptions"]

        KEYS = {
            "{space}": " ",
        }

        try:
            del exceptions["__name__"]
        except KeyError:
            pass

        for k in KEYS:
            try:
                exceptions[KEYS[k]] = exceptions.pop(k)
            except KeyError:
                pass

        return exceptions

# !TODO cache the following, to not recreate it on every call
    @property
    def get_configured_tags(self):
        """
            return all configured tags to be able to overwrite certain
            tags via a configuration file (e.g. id.txt)
        """
        tags = self.config._sections["tags"]

        try:
            del tags["__name__"]
        except KeyError:
            pass

        return tags