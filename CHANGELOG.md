# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Nothing yet

### Changed
- Nothing yet

### Deprecated
- Nothing yet

### Removed
- Nothing yet

### Fixed
- Nothing yet

### Security
- Nothing yet

## [1.2.0] - 2026-06-12

### Added
- Icon caching system with SQLite database
- Async bookmark validation with progress bar
- Support for multiple browser formats (Chrome, Firefox, Edge)
- Export to multiple formats (Markdown, CSV, JSON, OPML)
- Cache management commands (--clear-cache, --cache-stats)

### Changed
- Improved CLI with more options
- Better error handling for validation

### Features
- **Cache Module**: Local icon cache using SQLite
- **Validator Module**: Async bookmark URL validation
- **Exporters Module**: Multi-format export support

## [1.1.0] - 2026-06-12

### Added
- Async icon downloading for better performance
- Progress bar for long-running operations
- Configuration file support (`config.json`)
- Bookmark deduplication
- Background image download for portal page
- Beautiful portal HTML page with bookmark cards

### Changed
- Improved download performance with concurrent requests
- Enhanced CLI with progress display
- Better error handling for network issues

### Features
- **Async Downloader**: Concurrent icon downloads using asyncio
- **Progress Bar**: Real-time progress display with tqdm
- **Config File**: JSON-based configuration file support
- **Deduplication**: Automatic removal of duplicate bookmarks

## [1.0.0] - 2026-06-11

### Added
- Initial release
- Parse iTab backup files (`.itabdata`)
- Download website icons from iTab CDN
- Generate Chrome-compatible bookmark files (HTML & JSON)
- Create icon mapping for bookmark customization
- Command-line interface (`itab-migration` command)
- Python API for programmatic usage
- Support for multiple icon formats (SVG, PNG, ICO, WebP)
- Rate limiting for icon downloads
- Comprehensive error handling
- Detailed logging
- Examples and documentation

### Features
- **Parser Module**: Extracts bookmark data from iTab backup files
- **Downloader Module**: Downloads icons with retry logic and rate limiting
- **Generator Module**: Creates Chrome-compatible bookmark files
- **CLI Module**: Command-line interface with full option support
- **Migrator Module**: High-level API for easy migration

### Documentation
- README with usage instructions
- API reference documentation
- Examples for basic and advanced usage
- Contributing guidelines

## [0.1.0] - 2026-06-11 (Pre-release)

### Added
- Initial development version
- Basic parsing functionality
- Icon download capability
- HTML bookmark generation

---

## Release Notes

### v1.0.0

This is the first stable release of iTab Migration Tool. It provides a complete
solution for migrating iTab bookmarks and icons to Chrome browser.

**Key Features:**
- Easy-to-use command-line interface
- Python API for integration with other tools
- Comprehensive error handling and logging
- Support for all iTab bookmark formats
- Automatic icon downloading and mapping

**Breaking Changes:**
- None (initial release)

**Upgrade Guide:**
- N/A (initial release)

---

## Version History

| Version | Date | Description |
|---------|------|-------------|
| 1.2.0 | 2026-06-12 | Icon cache, validation, multi-format export |
| 1.1.0 | 2026-06-12 | Async downloads, progress bar, config file, deduplication |
| 1.0.0 | 2026-06-11 | First stable release |
| 0.1.0 | 2026-06-11 | Pre-release |

---

## Future Plans

### v2.0.0 (Future)
- [ ] GUI interface
- [ ] Browser extension
- [ ] Cloud sync support
- [ ] Plugin system

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for details on how to contribute to this project.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
