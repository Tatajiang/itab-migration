"""
iTab backup file parser module.

This module provides functionality to parse iTab backup files (.itabdata)
and extract bookmark data including URLs, icons, and categories.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


@dataclass
class BookmarkItem:
    """Represents a single bookmark item from iTab backup."""
    
    id: str
    name: str
    url: str
    category: str
    icon_type: str = "icon"
    icon_url: str = ""
    icon_text: str = ""
    background_color: str = "#ffffff"
    view_count: int = 0
    
    @property
    def has_icon(self) -> bool:
        """Check if the bookmark has an icon URL."""
        return bool(self.icon_url and self.icon_url.startswith("http"))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert bookmark item to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "url": self.url,
            "category": self.category,
            "type": self.icon_type,
            "src": self.icon_url,
            "iconText": self.icon_text,
            "backgroundColor": self.background_color,
            "view": self.view_count,
        }


@dataclass
class ITABBackupData:
    """Represents the complete iTab backup data."""
    
    bookmarks: List[BookmarkItem] = field(default_factory=list)
    categories: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def total_count(self) -> int:
        """Get total number of bookmarks."""
        return len(self.bookmarks)
    
    @property
    def bookmarks_with_icons(self) -> List[BookmarkItem]:
        """Get bookmarks that have icon URLs."""
        return [b for b in self.bookmarks if b.has_icon]
    
    @property
    def bookmarks_without_icons(self) -> List[BookmarkItem]:
        """Get bookmarks without icon URLs."""
        return [b for b in self.bookmarks if not b.has_icon]
    
    def get_bookmarks_by_category(self, category: str) -> List[BookmarkItem]:
        """Get all bookmarks in a specific category."""
        return [b for b in self.bookmarks if b.category == category]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the backup data."""
        icon_sources = {}
        for bookmark in self.bookmarks_with_icons:
            try:
                domain = bookmark.icon_url.split("/")[2]
                icon_sources[domain] = icon_sources.get(domain, 0) + 1
            except (IndexError, AttributeError):
                pass
        
        return {
            "total_bookmarks": self.total_count,
            "bookmarks_with_icons": len(self.bookmarks_with_icons),
            "bookmarks_without_icons": len(self.bookmarks_without_icons),
            "categories": self.categories,
            "icon_sources": icon_sources,
        }


class ITABParser:
    """
    Parser for iTab backup files.
    
    This class parses .itabdata files exported from iTab browser extension
    and extracts bookmark information including URLs, icons, and categories.
    
    Example:
        >>> parser = ITABParser()
        >>> data = parser.parse("backup.itabdata")
        >>> print(f"Found {data.total_count} bookmarks")
    """
    
    def __init__(self):
        """Initialize the parser."""
        self._raw_data: Optional[Dict[str, Any]] = None
    
    def parse(self, file_path: str | Path) -> ITABBackupData:
        """
        Parse an iTab backup file.
        
        Args:
            file_path: Path to the .itabdata file
            
        Returns:
            ITABBackupData object containing parsed bookmarks
            
        Raises:
            FileNotFoundError: If the file does not exist
            json.JSONDecodeError: If the file is not valid JSON
            ValueError: If the file format is invalid
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Backup file not found: {file_path}")
        
        if not file_path.suffix == ".itabdata":
            raise ValueError(f"Invalid file extension: {file_path.suffix}. Expected .itabdata")
        
        with open(file_path, "r", encoding="utf-8") as f:
            self._raw_data = json.load(f)
        
        return self._parse_data()
    
    def parse_from_dict(self, data: Dict[str, Any]) -> ITABBackupData:
        """
        Parse iTab data from a dictionary.
        
        Args:
            data: Dictionary containing iTab backup data
            
        Returns:
            ITABBackupData object containing parsed bookmarks
        """
        self._raw_data = data
        return self._parse_data()
    
    def _parse_data(self) -> ITABBackupData:
        """Parse the raw data into structured format."""
        if not self._raw_data:
            raise ValueError("No data to parse. Call parse() first.")
        
        nav_config = self._raw_data.get("navConfig", [])
        bookmarks = []
        categories = []
        
        for category_data in nav_config:
            category_name = category_data.get("name", "Unknown")
            categories.append(category_name)
            
            children = category_data.get("children", [])
            
            for item in children:
                bookmark = BookmarkItem(
                    id=item.get("id", ""),
                    name=item.get("name", ""),
                    url=item.get("url", ""),
                    category=category_name,
                    icon_type=item.get("type", "icon"),
                    icon_url=item.get("src", ""),
                    icon_text=item.get("iconText", ""),
                    background_color=item.get("backgroundColor", "#ffffff"),
                    view_count=item.get("view", 0),
                )
                bookmarks.append(bookmark)
        
        metadata = {
            key: value for key, value in self._raw_data.items()
            if key != "navConfig"
        }
        
        return ITABBackupData(
            bookmarks=bookmarks,
            categories=categories,
            metadata=metadata,
        )
    
    def get_raw_data(self) -> Optional[Dict[str, Any]]:
        """Get the raw parsed data."""
        return self._raw_data
