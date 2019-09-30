# import os
# import errno
# import logging
#
# from configparser import RawConfigParser
#
# import pysplitcue
#
# logger = logging
# #.getLogger(__name__)
#
# class split_cue(object):
#
#     def __init__(self, cue, format, output, input):
#         self.cue = cue
#         self.format = format
#         self.input = input
#         self.output = output
#
#     def split(self):
#         result = pysplitcue -o self.format -i self.cue
#         return result
