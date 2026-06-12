"""
iTab Migration Tool
==================

A tool to migrate iTab bookmarks and icons to Chrome browser.

This package provides functionality to:
- Parse iTab backup files (.itabdata)
- Extract and download website icons
- Generate Chrome-compatible bookmark files
- Create icon mapping for bookmark customization

Example usage:
    >>> from itab_migration import ITabMigrator
    >>> migrator = ITabMigrator("backup.itabdata")
    >>> migrator.migrate()

For command-line usage:
    $ python -m itab_migration --input backup.itabdata --output ./output
"""

__version__ = "1.2.0"
__author__ = "Your Name"
__email__ = "TataJiang9527@gmail.com"
__license__ = "MIT"

from .migrator import ITabMigrator
from .parser import ITABParser
from .downloader import IconDownloader
from .async_downloader import AsyncIconDownloader
from .bookmark_generator import BookmarkGenerator
from .config import Config
from .deduplicator import deduplicate_bookmarks
from .cache import IconCache
from .validator import AsyncBookmarkValidator
from .exporters import export_bookmarks, get_supported_formats

__all__ = [
    "ITabMigrator",
    "ITABParser",
    "IconDownloader",
    "AsyncIconDownloader",
    "BookmarkGenerator",
    "Config",
    "deduplicate_bookmarks",
    "IconCache",
    "AsyncBookmarkValidator",
    "export_bookmarks",
    "get_supported_formats",
]
