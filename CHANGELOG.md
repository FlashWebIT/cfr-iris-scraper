# Change Log
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).
## [2.0.0] - 2019-08-16
### Changed
- Improved the scraper such that it makes use of the __VIEWSTATE variables passed down by the server.
- Ported all the code to Python for a more portable solution
- Improved performance relative to 1.x
- Changed the license.
### Added
- Multi-page train support
- Support for the average speed field
- Support for cancelled trains
- Station list endpoint
### Broke
- Removed all legacy JavaScript code.

## [1.0.1] - 2017-04-26
### Changed
- The JSON format for the station information, for consistency. This format is not compatible with version 1.0.0.
### Added
- Better error management
- Train information
- This CHANGELOG file.
### Fixed
- Fixed a bug which was preventing the use of the node server from another directory
- The server searches for PhantomJS and throws an error if it doesn't find it
### Broke
- Compatibility with the version 1.0.0 standard.

## 1.0.0 - Initial release