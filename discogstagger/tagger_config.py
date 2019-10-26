import os
import errno
import logging

import inspect

try:
    import configparser
except:
    from six.moves import configparser

from configparser import RawConfigParser

logger = logging
#.getLogger(__name__)

class memoized_property(object):

    def __init__(self, fget, doc=None):
        self.fget = fget
        self.__doc__ = doc or fget.__doc__
        self.__name__ = fget.__name__

    def __get__(self, obj, cls):
        if obj is None:
            return self
        obj.__dict__[self.__name__] = result = self.fget(obj)
        return result

class TaggerConfig(RawConfigParser):
    """ provides the configuration mechanisms for the discogstagger """

    def __init__(self, config_file):
        RawConfigParser.__init__(self, strict=False)
        self.read(os.path.join("conf", "default.conf"))
        self.read(config_file)

    @property
    def id_tag_name(self):
        source_name = self.get("source", "name")
        id_tag_name = self.get("source", source_name)

        return id_tag_name

    def get_without_quotation(self, section, name):
        config_value = self.get(section, name)
        return config_value.replace("\"", "")

    def get(self, section, name, **kw):
        config_value = RawConfigParser.get(self, section, name, raw=True)

        if config_value == "":
            config_value = None
        else:
            config_value = config_value.strip()

        return config_value

    def items(self, section, **kw):
        items = RawConfigParser.items(self, section, raw=True)
        return items

    @memoized_property
    def get_character_exceptions(self):
        """ placeholders for special characters within character exceptions. """


        exceptions = self._sections["character_exceptions"] if "character_exceptions" in self._sections else {}

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

    @memoized_property
    def get_configured_tags(self):
        """
            return all configured tags to be able to overwrite certain
            tags via a configuration file (e.g. id.txt)
        """
        tags = self._sections["tags"] if 'tags' in self._sections else {}

        try:
            del tags["__name__"]
        except KeyError:
            pass

        return tags
