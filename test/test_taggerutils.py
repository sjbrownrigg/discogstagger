#!/usr/bin/python
# -*- coding: utf-8 -*-
import os, sys
import logging

logging.basicConfig(level=10)
logger = logging.getLogger(__name__)

parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parentdir)

logger.debug("parentdir: %s" % parentdir)

#from discogstagger.taggerutils import TaggerUtils

def test_value_from_tag_format():
    assert True