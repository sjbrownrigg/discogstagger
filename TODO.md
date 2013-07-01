# discogstagger

## TODO List

### Version 1.2

- [X] Merge current latest version (branch: folder-jpeg) into master
- [X] Tag latest release on master
- [ ] Add documentation

### Version 2.0

- [ ] Refactor
- [ ] Add Unit-tests
- [X] Add layer in between discogs and the tags in files
- [X] Extend id.txt file to allow to use different tags and make the configuration
      easier (e.g. add sections and add source-tag)
- [X] Add migration script for current id.txt structure (easy)
- [ ] Adopt config option handling to allow for greater flexibility
- [ ] Add config option for user-agent string
- [ ] Add travis for continuous integration

### Later Versions (in no order)

- [ ] Add Rate-Limiting functionality for discogs
- [ ] Add different tagging-sources (e.g. AMG)
- [ ] Add batch processing functionality (scan directory tree and convert all
      found albums and tracks)
