# discogstagger

## TODO List

This list is here for historic reasons, all TODOs are now maintained in the github issues for this project. If you do have a new issue, just put it in the issues. This file is not maintained anymore.

### Version 1.2

- [x] Merge current latest version (branch: folder-jpeg) into master
- [x] Tag latest release on master

### Version 2.0

- [x] Refactor
- [x] Add Unit-tests
- [x] Add layer in between discogs and the tags in files
- [x] Extend id.txt file to allow to use different tags and make the configuration
      easier (e.g. add sections and add source-tag)
- [x] Add migration script for current id.txt structure (easy)
- [x] Adopt config option handling to allow for greater flexibility
- [x] Add config option for user-agent string
- [x] Add travis for continuous integration
- [x] Add batch processing functionality (scan directory tree and convert all
      found albums and tracks)

### Version 2.1

- [x] Provide authentication for downloading images
- [x] Add unit-tests for single disc albums
- [x] Allow different sources, not only discogs for the metadata
- [x] Add unit tests for different configuration in id.txt files
- [x] Adopt migration script according to the multi source stuff
- [x] Show help if no options are given on command line on using discogs_tagger
- [x] Rename discogs_tagger.py to discogstagger2.py (we are something different now)
- [x] Add error-handling to tagger_config, do not break execution, if empty id.txt file is read in tagger_config
- [x] Fix authentication problem - no need to authenticate every time
- [x] Recalculate remaining RateLimit seconds to hours and minutes (and seconds)
- [x] Adopt logging to show time as well
- [x] Adopt logging to use not only debug level, allow logging to file
- [x] Add error-handling for problems with disc (e.g. wrong source dir, like mentioned above), no need to
      break tagging, just report error
- [x] handle multi disc recognition, furthermore handle multi tracks with different "subtracks"
      (e.g. http://www.discogs.com/release/513904)
- [x] adopt setup.py - bump version, adopt other tags as well to use own repository
- [x] create github release
- [x] add possibility to split tags (e.g. artists) to provide an array to tags instead of a single string
      (resolved using split_tags.py, quite dirty, but it works),
- [x] Add Rate-Limiting functionality for discogs

### Version 2.2

- [ ] Add documentation
- [X] move from TODO.md to github issues
- [X] use new discogs client
- [ ] Minor Refactoring to avoid multiple checking of disc.target_dir and
      disc.sourcedir != None (taggerutils.py)
- [ ] Add progress bar for album art processing
- [ ] add "local" datasource, reuse DummyResponse from tests, needed to easily work around errors (see #7)
- [ ] add possibility to only tag files without moving/copying them (just leave them where they are)
- [X] adopt setup.py - bump version, adopt other tags as well to use own repository
- [X] add replay_gain possibility

### Later Versions (in no order)

- [ ] Add different external tagging-sources (e.g. AMG)
