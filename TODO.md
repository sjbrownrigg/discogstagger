# discogstagger

## TODO List

### Version 1.2

- [x] Merge current latest version (branch: folder-jpeg) into master
- [x] Tag latest release on master
- [ ] Add documentation

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

- [ ] Provide authentication for downloading images
- [ ] Minor Refactoring to avoid multiple checking of disc.target_dir and
      disc.sourcedir != None (taggerutils.py)
- [ ] Add unit-tests for single disc albums
- [X] Allow different sources, not only discogs for the metadata
- [X] Add unit tests for different configuration in id.txt files
- [ ] Adopt migration script according to the multi source stuff
- [ ] Show help if no options are given on command line on using discogs_tagger
- [ ] Add progress bar for album art processing

### Later Versions (in no order)

- [ ] Add Rate-Limiting functionality for discogs
- [ ] Add different tagging-sources (e.g. AMG)
