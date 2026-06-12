"""
Browser format support module.

This module provides functionality to export bookmarks in various
browser formats (Chrome, Firefox, Edge).
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime
from abc import ABC, abstractmethod

from .parser import BookmarkItem, ITABBackupData

logger = logging.getLogger(__name__)


class BrowserExporter(ABC):
    """Abstract base class for browser exporters."""
    
    @abstractmethod
    def export(self, data: ITABBackupData, output_path: Path) -> Path:
        """
        Export bookmarks to browser format.
        
        Args:
            data: Parsed iTab backup data
            output_path: Path to save the exported file
            
        Returns:
            Path to the exported file
        """
        pass
    
    @staticmethod
    def _escape_html(text: str) -> str:
        """Escape HTML special characters."""
        return (
            text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#39;")
        )


class ChromeExporter(BrowserExporter):
    """Export bookmarks in Chrome format."""
    
    def export(self, data: ITABBackupData, output_path: Path) -> Path:
        """Export to Chrome JSON format."""
        from .bookmark_generator import BookmarkGenerator
        generator = BookmarkGenerator()
        return generator.generate_json(data, output_path)


class FirefoxExporter(BrowserExporter):
    """Export bookmarks in Firefox format."""
    
    def export(self, data: ITABBackupData, output_path: Path) -> Path:
        """
        Export to Firefox bookmarks HTML format.
        
        Firefox uses the Netscape Bookmark File Format,
        which is the same as Chrome's HTML export.
        """
        from .bookmark_generator import BookmarkGenerator
        generator = BookmarkGenerator()
        return generator.generate_html(data, output_path, title="Firefox Bookmarks")


class EdgeExporter(BrowserExporter):
    """Export bookmarks in Edge format."""
    
    def export(self, data: ITABBackupData, output_path: Path) -> Path:
        """
        Export to Edge JSON format.
        
        Edge uses the same format as Chrome (Chromium-based).
        """
        from .bookmark_generator import BookmarkGenerator
        generator = BookmarkGenerator()
        return generator.generate_json(data, output_path)


class MarkdownExporter(BrowserExporter):
    """Export bookmarks in Markdown format."""
    
    def export(self, data: ITABBackupData, output_path: Path) -> Path:
        """
        Export to Markdown format.
        
        Creates a structured Markdown document with bookmarks
        organized by category.
        """
        output_path = Path(output_path)
        
        lines = [
            "# 书签导出",
            "",
            f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"书签总数: {data.total_count}",
            "",
            "---",
            "",
        ]
        
        # Group by category
        categories: Dict[str, List[BookmarkItem]] = {}
        for bookmark in data.bookmarks:
            if bookmark.category not in categories:
                categories[bookmark.category] = []
            categories[bookmark.category].append(bookmark)
        
        # Generate Markdown
        for category, bookmarks in categories.items():
            lines.append(f"## {category}")
            lines.append("")
            
            for bookmark in bookmarks:
                if bookmark.url:
                    lines.append(f"- [{bookmark.name}]({bookmark.url})")
            
            lines.append("")
        
        # Write to file
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        
        logger.info(f"Exported to Markdown: {output_path}")
        return output_path


class CSVExporter(BrowserExporter):
    """Export bookmarks in CSV format."""
    
    def export(self, data: ITABBackupData, output_path: Path) -> Path:
        """
        Export to CSV format.
        
        Creates a CSV file with columns: name, url, category, icon_url
        """
        import csv
        
        output_path = Path(output_path)
        
        with open(output_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            
            # Header
            writer.writerow(["name", "url", "category", "icon_url"])
            
            # Data
            for bookmark in data.bookmarks:
                if bookmark.url:
                    writer.writerow([
                        bookmark.name,
                        bookmark.url,
                        bookmark.category,
                        bookmark.icon_url,
                    ])
        
        logger.info(f"Exported to CSV: {output_path}")
        return output_path


class JSONExporter(BrowserExporter):
    """Export bookmarks in JSON format."""
    
    def export(self, data: ITABBackupData, output_path: Path) -> Path:
        """
        Export to JSON format.
        
        Creates a JSON file with structured bookmark data.
        """
        output_path = Path(output_path)
        
        export_data = {
            "export_time": datetime.now().isoformat(),
            "total_bookmarks": data.total_count,
            "categories": data.categories,
            "bookmarks": [
                {
                    "id": b.id,
                    "name": b.name,
                    "url": b.url,
                    "category": b.category,
                    "icon_url": b.icon_url,
                    "background_color": b.background_color,
                }
                for b in data.bookmarks
                if b.url
            ],
        }
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Exported to JSON: {output_path}")
        return output_path


class OPMLExporter(BrowserExporter):
    """Export bookmarks in OPML format."""
    
    def export(self, data: ITABBackupData, output_path: Path) -> Path:
        """
        Export to OPML format.
        
        OPML (Outline Processor Markup Language) is used by
        RSS readers and outliners.
        """
        output_path = Path(output_path)
        
        lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<opml version="2.0">',
            '  <head>',
            f'    <title>iTab Bookmarks Export</title>',
            f'    <dateCreated>{datetime.now().isoformat()}</dateCreated>',
            '  </head>',
            '  <body>',
        ]
        
        # Group by category
        categories: Dict[str, List[BookmarkItem]] = {}
        for bookmark in data.bookmarks:
            if bookmark.category not in categories:
                categories[bookmark.category] = []
            categories[bookmark.category].append(bookmark)
        
        # Generate OPML
        for category, bookmarks in categories.items():
            lines.append(f'    <outline text="{self._escape_html(category)}">')
            
            for bookmark in bookmarks:
                if bookmark.url:
                    lines.append(
                        f'      <outline text="{self._escape_html(bookmark.name)}" '
                        f'url="{self._escape_html(bookmark.url)}"/>'
                    )
            
            lines.append('    </outline>')
        
        lines.extend([
            '  </body>',
            '</opml>',
        ])
        
        # Write to file
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        
        logger.info(f"Exported to OPML: {output_path}")
        return output_path


# Registry of exporters
EXPORTERS: Dict[str, type] = {
    "chrome": ChromeExporter,
    "firefox": FirefoxExporter,
    "edge": EdgeExporter,
    "markdown": MarkdownExporter,
    "csv": CSVExporter,
    "json": JSONExporter,
    "opml": OPMLExporter,
}


def get_exporter(format_name: str) -> BrowserExporter:
    """
    Get exporter by format name.
    
    Args:
        format_name: Name of the export format
        
    Returns:
        BrowserExporter instance
        
    Raises:
        ValueError: If format is not supported
    """
    format_name = format_name.lower()
    
    if format_name not in EXPORTERS:
        supported = ", ".join(EXPORTERS.keys())
        raise ValueError(f"Unsupported format: {format_name}. Supported: {supported}")
    
    return EXPORTERS[format_name]()


def export_bookmarks(
    data: ITABBackupData,
    format_name: str,
    output_path: str | Path,
) -> Path:
    """
    Export bookmarks in specified format.
    
    Args:
        data: Parsed iTab backup data
        format_name: Name of the export format
        output_path: Path to save the exported file
        
    Returns:
        Path to the exported file
    """
    exporter = get_exporter(format_name)
    return exporter.export(data, Path(output_path))


def get_supported_formats() -> List[str]:
    """Get list of supported export formats."""
    return list(EXPORTERS.keys())
