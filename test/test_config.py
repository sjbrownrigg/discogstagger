import os, sys
import logging

logging.basicConfig(level=10)
logger = logging.getLogger(__name__)

parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parentdir)

logger.debug("parentdir: %s" % parentdir)

from discogstagger.tagger_config import TaggerConfig

def test_default_values():

    tagger_config = TaggerConfig(os.path.join(parentdir, "test/empty.conf"))
    config = tagger_config.config

    assert config.getboolean("details", "keep_original")
    assert not config.getboolean("details", "use_style")
    assert config.getboolean("details", "use_lower_filenames")

    assert config.get("file-formatting", "images") == "image"

def test_set_values():

    tagger_config = TaggerConfig(os.path.join(parentdir, "test/test_values.conf"))
    config = tagger_config.config

    assert not config.getboolean("details", "keep_original")
    assert config.getboolean("details", "use_style")

    assert config.get("file-formatting", "images") == "XXIMGXX"

    # not overwritten value should stay the same
    assert config.getboolean("details", "use_lower_filenames")
