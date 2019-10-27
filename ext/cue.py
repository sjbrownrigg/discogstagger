#!/usr/bin/env python3
# This Python file uses the following encoding: utf-8

# CUE-sheet file syntax can be found here:
# http://digitalx.org/cue-sheet/syntax/

import chardet
import codecs
import tempfile
import os

allowed_formats = ["BINARY", "MOTOROLA", "AIFF", "WAVE", "MP3"]
allowed_flags = ["DCP", "4CH", "PRE", "SCMS"]
allowed_datatypes = ["AUDIO", "CDG", "MODE1/2048", "MODE1/2352", \
"MODE2/2336", "MODE2/2352", "CDI/2336", "CDI/2352"]
allowed_extensions = ('.flac', '.wav', '.ape', '.alac', '.wv')

class Track:
    def __init__(self):
        self.flags = []
        self.indexes = []
        self.isrc = None
        self.performer = None
        self.pregap = None
        self.postgap = None
        self.songwriter = None
        self.title = None
        self.number = None
        self.datatype = None

class CUE:
    def __init__(self, file_name):
        self.file_name = file_name
        self.file_encoding = self.file_encoding()
        self.content = None
        self.load()
        self.parse()

    def __str__(self):
        return self.content

    def load(self):
        with open(self.file_name, 'r', encoding=self.file_encoding) as f:
            self.content = f.readlines()
            self.content = [ x.replace("/","\\") for x in self.content]

    def parse(self):
        scope = 'global'
        # Initilizing attributes
        self.tracks = []
        self.remarks = []
        self.catalog_number = None
        self.cdtext_file_name = None
        self.image_file_format = None
        self.image_file_name = None
        self.image_file_directory = None
        self.performer = None
        self.songwriter = None
        self.title = None
        self.discnumber = None
        self.disctotal = None
        self.genre = None
        self.date = None
        self.discid = None
        self.comment = None
        # Leaving first track blank
        current_track = Track()
        stripped_content = [l.strip() for l in self.content]
        # Parsing all posible lines
        for line in stripped_content:
            cmd = line.split(" ")[0]
            if cmd=="CATALOG":
                self.catalog_number = line.split(" ")[1]
                if not len(self.catalog_number)==13:
                    print("WARNING: Catalog number has incorrect length")
            if cmd=="CDTEXTFILE":
                value = line.split(" ")[1]
                if value[0] == '"': value = value[1:]
                if value[-1] == '"': value = value[:-1]
                self.cdtext_file_name = value
            if cmd=="FILE":
                file_name_value = line[5:]
                format_value = file_name_value.split(" ")[-1]
                self.image_file_format = format_value.upper()
                z = len(format_value) + 1 # +1 is for space
                file_name_value = file_name_value[:-z]
                if file_name_value[0] == '"':
                    file_name_value = file_name_value[1:]
                if file_name_value[-1] == '"':
                    file_name_value = file_name_value[:-1]
                # Add dirname of CUE file if path to image is relative
                if os.path.dirname(file_name_value)=="":
                    file_name_value = os.path.join( \
                            os.path.dirname(self.file_name), \
                            file_name_value)
                self.image_file_directory = os.path.dirname(self.file_name)
                if os.path.exists(file_name_value):
                    self.image_file_name = file_name_value
                else:
                    self.image_file_name = self.locate_image(file_name_value)
                if self.image_file_directory is None:
                    print("WARNING: image file not found: {}".format(file_name_value))
                if not self.image_file_format in allowed_formats:
                    print("WARNING: Image format %s is not allowed" % \
                    self.image_file_format)
            if cmd=="FLAGS":
                current_track.flags = [x.upper() for x in line.split(" ")[1:]]
                for flag in current_track.flags:
                    if not self.image_file_format in allowed_formats:
                        print("WARNING: Flag %s is not allowed" % flag)
            if cmd=="INDEX":
                current_track.indexes.append(\
                (line.split(" ")[1], line.split(" ")[2]))
                if int(line.split(" ")[1])<0 or int(line.split(" ")[1])>99:
                    print("WARNING: Index number %s is not allowed" % \
                    line.split(" ")[1])
            if cmd=="ISRC":
                current_track.isrc = line.split(" ")[1]
                if not len(line.split(" ")[1]) == 12:
                    print("WARNING: ISRC must be 12 characters in length")
            if cmd=="PERFORMER":
                value = line[11:]
                if value[0] == '"': value = value[1:]
                if value[-1] == '"': value = value[:-1]
                if scope=="global":
                    self.performer = value
                if scope=="track":
                    current_track.performer = value
                if len(value)>80:
                    print("WARNING: Performer name should be limited \
                    to 80 character or less")
            if cmd=="POSTGAP":
                current_track.postgap = line.split(" ")[1]
            if cmd=="PREGAP":
                current_track.pregap = line.split(" ")[1]
            if cmd=="REM":
                # TODO: Implement custom encoders' tags written as REMs
                self.remarks.append(line[4:])
            if line.startswith("REM GENRE"):
                self.genre = line[10:]
            if line.startswith("REM DATE"):
                self.date = line[9:]
            if line.startswith("REM DISCID"):
                self.discid = line[11:]
            if line.startswith("REM COMMENT"):
                value = line[11:]
                if value[0] == '"': value = value[1:]
                if value[-1] == '"': value = value[:-1]
                self.comment = value
            if cmd=="SONGWRITER":
                value = line[11:]
                if value[0] == '"': value = value[1:]
                if value[-1] == '"': value = value[:-1]
                if scope=="global":
                    self.songwriter = value
                if scope=="track":
                    current_track.songwriter = value
                if len(value)>80:
                    print("WARNING: Songwriter name should be limited \
                    to 80 character or less")
            if cmd=="TITLE":
                value = line[6:]
                if value[0] == '"': value = value[1:]
                if value[-1] == '"': value = value[:-1]
                if scope=="global":
                    self.title = value
                if scope=="track":
                    current_track.title = value
                if len(value)>80:
                    print("WARNING: Title should be limited \
                    to 80 character or less")
            if cmd=="DISCID":
                value = line[7:]
                if value[0] == '"': value = value[1:]
                if value[-1] == '"': value = value[:-1]
                if scope=="global":
                    self.discid = value
                if scope=="track":
                    current_track.discid = value
            if cmd=="DISCNUMBER":
                value = line[11:]
                if value[0] == '"': value = value[1:]
                if value[-1] == '"': value = value[:-1]
                if scope=="global":
                    self.discnumber = value
                if scope=="track":
                    current_track.discnumber = value
            if cmd=="TRACK":
                scope = "track"
                self.tracks.append(current_track)
                current_track = Track()
                current_track.number = int(line.split(" ")[1])
                current_track.datatype = line.split(" ")[2].upper()
                if current_track.number<1 or current_track.number>99:
                    print("WARNING: Track number must be between 1 and \
                    99 inclusive")
                if not current_track.datatype in allowed_datatypes:
                    print("WARNING: Track datatype %s is not allowed" \
                    % current_track.datatype)
        self.tracks.append(current_track)

    def locate_image(self, file_name_value):
        ''' Sometimes files are compressed after CUE has been created,
            but the FILE details have not been updated
        '''
        file = os.path.split(file_name_value)[1]
        file_name = os.path.splitext(file)[0]
        for r, d, f in os.walk(self.image_file_directory):
            for file in f:
                if file.startswith(file_name) and file.endswith(allowed_extensions):
                    if os.path.exists(os.path.join(self.image_file_directory, file)):
                        return os.path.join(self.image_file_directory, file)

    def file_encoding(self):
        with open(self.file_name,'rb') as f:
            data = f.read()
            return chardet.detect(data).get("encoding")

    def get_temporary_copy(self):
        (fd, fname) = tempfile.mkstemp(suffix='.cue', prefix='tmp', dir='/tmp', text=True)
        f = codecs.open(fname, encoding='utf-8', mode='w')
        for line in self.content:
            f.write(line)
        f.close()
        return fname
