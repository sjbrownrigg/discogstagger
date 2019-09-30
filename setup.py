NAME = "discogstagger2"
VERSION = "2.2.0"

from distutils.core import setup

setup (
    name = NAME,
    version = VERSION,
    description = ("Console based audio-file metadata tagger that uses the Discogs.com api"),
    author = "Markus M. May",
    author_email = "triplem@javafreedom.org",
    url = "https://github.com/triplem/discogstagger",
    scripts = ["discogstagger2.py"],
    packages = ["discogstagger", "ext"],
    data_files = [(
        "/etc/%s/" % NAME, ["conf/discogs_tagger.conf"]),
        ("share/%s" % NAME, ["README.md"])]
)
