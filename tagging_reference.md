# Title formatting reference
# http://wiki.hydrogenaud.io/index.php?title=Foobar2000:Title_Formatting_Reference#Track_info_fields_and_functions

%album artist%
%albumartist%
%album%
%artist%
%discnumber%
%totaldiscs%
%track artist%
%title%
%tracknumber%
%track number%
%bitrate%
%channels%
%codec%
%filesize%
%filesize_natural%
%length%
%length_ex%
%length_seconds%
%length_seconds_fp%
%length_samples%
%samplerate%


















%album artist%
Name of the artist of the album specified track belongs to. Checks following metadata fields, in this order: "album artist", "artist", "composer", "performer". The difference between this and %artist% is that %album artist% is intended for use where consistent value across entire album is needed even when per-track artists values vary.

%album%
Name of the album specified track belongs to. Checks following metadata fields, in this order: "album", "venue".

%artist%
Name of the artist of the track. Checks following metadata fields, in this order: "artist", "album artist", "composer", "performer". For a SHOUTcast stream which contains metadata, it is the StreamTitle up to the first "-" character.

%discnumber%
Index of disc specified track belongs to, within the album. Available only when "discnumber"/"disc" field is present in track’s metadata.

%totaldiscs%
Index of total discs specified tracks belong to, within the album. Available only when "discnumber"/"disc" field is present in track’s metadata.

%track artist%
Name of the artist of the track; present only if %album artist% is different than %artist% for specific track. Intended for use together with %album artist%, to indicate track-specific artist info, e.g. "%album artist% - %title%[ '//' %track artist%]". In this case, the last part will be displayed only when track-specific artist info is present.

%title%
Title of the track. If "title" metadata field is missing, file name is used instead. For a SHOUTcast stream which contains metadata, it is the StreamTitle after the first "-" character.

%tracknumber%
Two-digit index of specified track within the album. Available only when "tracknumber" field is present in track’s metadata. An extra '0' is placed in front of single digit track numbers (5 becomes 05).

%track number%
Similar to %tracknumber%, however single digit track numbers are not reformatted to have an extra 0.

Technical information fields
%bitrate%
Bitrate of the track in kilobits per second. VBR files will show a dynamic display for currently played track (outside of the playlist).

%channels%
Number of channels in the track, as text; either "mono", "stereo" for 1 or 2 channels, respectively, otherwise a number followed by "ch", e.g. "6ch".

%codec%
Name of codec used to encode the track, e.g. PCM, FLAC, MP3, or AAC. If exact codec name is not available, file extension is used. The Default UI's standard Codec column displays the same info, but sometimes adds details, e.g. "MP3 / VBR V2" or "AAC / LC".

%filesize%
The exact file size in bytes. Old version: %_filesize%

%filesize_natural%
The approximate file size, automatically formatted in appropriate units such as megabytes or kilobytes, e.g. "8.49 MB"

%length%
The length of the track formatted as hours, minutes, and seconds, rounded to the nearest second. Old version: %_time_total%

%length_ex%
The length of the track formatted as hours, minutes, seconds, and milliseconds, rounded to the nearest millisecond.

%length_seconds%
The length of the track in seconds, rounded to the nearest second. Old version: %_time_total_seconds%

%length_seconds_fp%
The length of the track in seconds as a floating point number.

%length_samples%
The length of the track in samples.

%samplerate%
