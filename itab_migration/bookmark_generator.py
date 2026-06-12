"""
Bookmark generator module.

This module provides functionality to generate Chrome-compatible bookmark
files from parsed iTab backup data.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from .parser import BookmarkItem, ITABBackupData

logger = logging.getLogger(__name__)


class BookmarkGenerator:
    """
    Generates Chrome-compatible bookmark files.
    
    This class creates bookmark files in various formats that can be
    imported into Google Chrome browser.
    
    Supported formats:
        - HTML (Netscape Bookmark File Format)
        - JSON (Chrome native format)
    
    Example:
        >>> generator = BookmarkGenerator()
        >>> generator.generate_html(data, "bookmarks.html")
        >>> generator.generate_json(data, "bookmarks.json")
    """
    
    def __init__(self):
        """Initialize the bookmark generator."""
        self._bookmark_id_counter = 1000
    
    def _get_next_id(self) -> str:
        """Generate next bookmark ID."""
        self._bookmark_id_counter += 1
        return str(self._bookmark_id_counter)
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in Chrome format."""
        # Chrome uses microseconds since January 1, 1601
        # This is a simplified version using current time
        return str(int(datetime.now().timestamp() * 1000000))
    
    def generate_html(
        self,
        data: ITABBackupData,
        output_path: str | Path,
        title: str = "Bookmarks",
    ) -> Path:
        """
        Generate HTML bookmark file (Netscape Bookmark File Format).
        
        This format can be imported into Chrome using:
            Chrome -> Bookmarks -> Import bookmarks and settings
        
        Args:
            data: Parsed iTab backup data
            output_path: Path to save the HTML file
            title: Title for the bookmark file
            
        Returns:
            Path to the generated file
        """
        output_path = Path(output_path)
        
        # Build HTML content
        html_lines = [
            '<!DOCTYPE NETSCAPE-Bookmark-file-1>',
            '<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">',
            f'<TITLE>{title}</TITLE>',
            f'<H1>{title}</H1>',
            '<DL><p>',
        ]
        
        # Group bookmarks by category
        categories: Dict[str, List[BookmarkItem]] = {}
        for bookmark in data.bookmarks:
            if bookmark.category not in categories:
                categories[bookmark.category] = []
            categories[bookmark.category].append(bookmark)
        
        # Generate HTML for each category
        for category_name, bookmarks in categories.items():
            html_lines.append(f'    <DT><H3>{self._escape_html(category_name)}</H3>')
            html_lines.append('    <DL><p>')
            
            for bookmark in bookmarks:
                if bookmark.url:
                    escaped_name = self._escape_html(bookmark.name)
                    escaped_url = self._escape_html(bookmark.url)
                    html_lines.append(
                        f'        <DT><A HREF="{escaped_url}">{escaped_name}</A>'
                    )
            
            html_lines.append('    </DL><p>')
        
        html_lines.append('</DL><p>')
        
        # Write to file
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(html_lines))
        
        logger.info(f"Generated HTML bookmarks: {output_path}")
        return output_path
    
    def generate_json(
        self,
        data: ITABBackupData,
        output_path: str | Path,
    ) -> Path:
        """
        Generate JSON bookmark file (Chrome native format).
        
        This format can be used to directly replace Chrome's bookmark file.
        Location: C:\\Users\\<user>\\AppData\\Local\\Google\\Chrome\\User Data\\Default\\Bookmarks
        
        Args:
            data: Parsed iTab backup data
            output_path: Path to save the JSON file
            
        Returns:
            Path to the generated file
        """
        output_path = Path(output_path)
        
        # Build Chrome bookmark structure
        bookmarks_json = {
            "checksum": "",
            "roots": {
                "bookmark_bar": {
                    "children": [],
                    "date_added": self._get_timestamp(),
                    "date_last_used": "0",
                    "date_modified": self._get_timestamp(),
                    "guid": "00000000-0000-0000-0000-000000000001",
                    "id": "1",
                    "name": "书签栏",
                    "type": "folder",
                },
                "other": {
                    "children": [],
                    "date_added": self._get_timestamp(),
                    "date_last_used": "0",
                    "date_modified": self._get_timestamp(),
                    "guid": "00000000-0000-0000-0000-000000000002",
                    "id": "2",
                    "name": "其他书签",
                    "type": "folder",
                },
                "synced": {
                    "children": [],
                    "date_added": self._get_timestamp(),
                    "date_last_used": "0",
                    "date_modified": self._get_timestamp(),
                    "guid": "00000000-0000-0000-0000-000000000003",
                    "id": "3",
                    "name": "移动设备书签",
                    "type": "folder",
                },
            },
            "version": 1,
        }
        
        # Group bookmarks by category
        categories: Dict[str, List[BookmarkItem]] = {}
        for bookmark in data.bookmarks:
            if bookmark.category not in categories:
                categories[bookmark.category] = []
            categories[bookmark.category].append(bookmark)
        
        # Add categories as folders to bookmark bar
        bookmark_bar = bookmarks_json["roots"]["bookmark_bar"]["children"]
        
        for category_name, bookmarks in categories.items():
            folder = {
                "children": [],
                "date_added": self._get_timestamp(),
                "date_last_used": "0",
                "date_modified": self._get_timestamp(),
                "guid": f"folder-{category_name}",
                "id": f"folder-{category_name}",
                "name": category_name,
                "type": "folder",
            }
            
            for bookmark in bookmarks:
                if bookmark.url:
                    bookmark_entry = {
                        "date_added": self._get_timestamp(),
                        "date_last_used": "0",
                        "guid": bookmark.id,
                        "id": bookmark.id,
                        "name": bookmark.name,
                        "type": "url",
                        "url": bookmark.url,
                    }
                    folder["children"].append(bookmark_entry)
            
            bookmark_bar.append(folder)
        
        # Write to file
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(bookmarks_json, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Generated JSON bookmarks: {output_path}")
        return output_path
    
    def generate_icon_mapping(
        self,
        data: ITABBackupData,
        download_results: List[Any],
        output_path: str | Path,
    ) -> Path:
        """
        Generate icon mapping file.
        
        This file maps bookmarks to their downloaded icon files,
        which can be used with Chrome extensions to set custom icons.
        
        Args:
            data: Parsed iTab backup data
            download_results: List of DownloadResult objects
            output_path: Path to save the mapping file
            
        Returns:
            Path to the generated file
        """
        output_path = Path(output_path)
        
        # Create mapping from download results
        result_map = {r.bookmark.id: r for r in download_results}
        
        mapping = []
        for bookmark in data.bookmarks:
            result = result_map.get(bookmark.id)
            
            entry = {
                "id": bookmark.id,
                "name": bookmark.name,
                "url": bookmark.url,
                "category": bookmark.category,
                "icon_url": bookmark.icon_url,
                "icon_file": str(result.local_path) if result and result.success else None,
                "background_color": bookmark.background_color,
                "has_icon": bookmark.has_icon,
            }
            mapping.append(entry)
        
        # Write to file
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(mapping, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Generated icon mapping: {output_path}")
        return output_path
    
    def generate_portal_html(
        self,
        data: ITABBackupData,
        output_path: str | Path,
        icons_dir: str | Path,
        title: str = "书签导航",
        background_image: str | Path | None = None,
    ) -> Path:
        """
        Generate a modern tech-style portal HTML page with bookmark cards.
        
        Design inspired by Linear + Raycast UI language.
        Features: dark theme, glassmorphism cards, global search, blue-purple gradients.
        
        Args:
            data: Parsed iTab backup data
            output_path: Path to save the HTML file
            icons_dir: Directory containing downloaded icons
            title: Page title
            background_image: Path to background image file (not used in this design)
            
        Returns:
            Path to the generated file
        """
        output_path = Path(output_path)
        icons_dir = Path(icons_dir)
        
        # Build icon path mapping
        icon_map = {}
        if icons_dir.exists():
            for icon_file in icons_dir.iterdir():
                if icon_file.is_file():
                    icon_map[icon_file.stem] = icon_file.name
        
        # Group bookmarks by category
        categories: Dict[str, List[BookmarkItem]] = {}
        for bookmark in data.bookmarks:
            if bookmark.category not in categories:
                categories[bookmark.category] = []
            categories[bookmark.category].append(bookmark)
        
        # Generate category sections
        category_sections = []
        for category_name, bookmarks in categories.items():
            cards = []
            for bookmark in bookmarks:
                if not bookmark.url:
                    continue
                
                # Get icon path
                icon_file = icon_map.get(bookmark.name, "")
                if icon_file:
                    icon_src = f"icons/{icon_file}"
                elif bookmark.icon_url:
                    icon_src = bookmark.icon_url
                else:
                    icon_src = ""
                
                # Generate icon element with fallback
                if icon_src:
                    icon_html = f'<img src="{self._escape_html(icon_src)}" alt="" >'
                else:
                    icon_html = f'<div class="icon-letter">{bookmark.name[0].upper()}</div>'
                
                card = f'''
                <a href="{self._escape_html(bookmark.url)}" class="card" target="_blank" rel="noopener noreferrer" data-name="{self._escape_html(bookmark.name.lower())}">
                    <div class="card-icon">
                        {icon_html}
                    </div>
                    <span class="card-name">{self._escape_html(bookmark.name)}</span>
                </a>'''
                cards.append(card)
            
            if cards:
                section = f'''
            <section class="category" data-category="{self._escape_html(category_name)}">
                <div class="category-header">
                    <div class="category-title">
                        <span class="category-dot"></span>
                        {self._escape_html(category_name)}
                    </div>
                    <span class="category-count">{len(cards)}</span>
                </div>
                <div class="category-divider"></div>
                <div class="cards-grid">
                    {"".join(cards)}
                </div>
            </section>'''
                category_sections.append(section)
        
        # Build complete HTML
        html_content = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self._escape_html(title)}</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
        
        :root {{
            --bg-page: #0A0E17;
            --bg-surface: rgba(255, 255, 255, 0.035);
            --bg-elevated: rgba(255, 255, 255, 0.05);
            --bg-hover: rgba(255, 255, 255, 0.07);
            --border-default: rgba(255, 255, 255, 0.06);
            --border-hover: rgba(139, 92, 246, 0.3);
            --border-subtle: rgba(255, 255, 255, 0.04);
            --text-primary: #E5E7EB;
            --text-secondary: #9CA3AF;
            --text-muted: #6B7280;
            --accent: #8B5CF6;
            --accent-dim: rgba(139, 92, 246, 0.06);
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        html {{
            font-size: 16px;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
        }}
        
        body {{
            font-family: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif;
            background: var(--bg-page);
            color: var(--text-primary);
            min-height: 100vh;
            padding: 28px 24px 64px;
            line-height: 1.5;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        
        /* Header */
        header {{
            text-align: center;
            margin-bottom: 20px;
        }}
        
        h1 {{
            font-size: 2.5rem;
            font-weight: 500;
            color: var(--text-primary);
            margin-bottom: 4px;
            letter-spacing: -0.02em;
        }}
        
        .subtitle {{
            color: var(--text-muted);
            font-size: 0.875rem;
            font-weight: 400;
        }}
        
        /* Search Box - Core entry */
        .search-wrapper {{
            max-width: 520px;
            margin: 0 auto 28px;
            position: relative;
        }}
        
        .search-input {{
            width: 100%;
            padding: 13px 64px 13px 44px;
            background: var(--bg-surface);
            border: 1px solid var(--border-default);
            border-radius: 10px;
            color: var(--text-primary);
            font-size: 0.9375rem;
            font-weight: 400;
            outline: none;
            transition: border-color 0.2s, box-shadow 0.2s;
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
        }}
        
        .search-input::placeholder {{
            color: var(--text-muted);
        }}
        
        .search-input:hover {{
            border-color: rgba(255, 255, 255, 0.1);
        }}
        
        .search-input:focus {{
            border-color: var(--border-hover);
            box-shadow: 0 0 0 3px var(--accent-dim);
        }}
        
        .search-icon {{
            position: absolute;
            left: 14px;
            top: 50%;
            transform: translateY(-50%);
            color: var(--text-muted);
            pointer-events: none;
            width: 18px;
            height: 18px;
            opacity: 0.6;
        }}
        
        .search-shortcut {{
            position: absolute;
            right: 14px;
            top: 50%;
            transform: translateY(-50%);
            padding: 2px 7px;
            background: rgba(255, 255, 255, 0.06);
            border: 1px solid var(--border-default);
            border-radius: 4px;
            color: var(--text-muted);
            font-size: 0.75rem;
            font-family: "SF Mono", "Fira Code", "Consolas", monospace;
            pointer-events: none;
        }}
        
        .search-results-count {{
            text-align: center;
            color: var(--text-muted);
            font-size: 0.625rem;
            margin-top: 6px;
            min-height: 14px;
        }}
        
        /* Categories */
        .category {{
            margin-bottom: 28px;
        }}
        
        .category-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 12px;
            padding: 0 4px;
        }}
        
        .category-title {{
            font-size: 0.875rem;
            font-weight: 500;
            color: var(--text-secondary);
            letter-spacing: 0.03em;
            display: flex;
            align-items: center;
            gap: 6px;
        }}
        
        .category-dot {{
            width: 5px;
            height: 5px;
            border-radius: 50%;
            background: var(--accent);
            opacity: 0.5;
        }}
        
        .category-count {{
            font-size: 0.5625rem;
            color: var(--text-muted);
            font-weight: 400;
            font-variant-numeric: tabular-nums;
        }}
        
        .category-divider {{
            height: 1px;
            background: var(--border-subtle);
            margin-bottom: 12px;
        }}
        
        /* Cards Grid */
        .cards-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(128px, 1fr));
            gap: 14px;
        }}
        
        /* Card - Light command tile */
        .card {{
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 10px;
            padding: 20px 10px 16px;
            background: var(--bg-surface);
            border: 1px solid var(--border-default);
            border-radius: 14px;
            text-decoration: none;
            color: var(--text-primary);
            transition: transform 0.15s, border-color 0.15s, background 0.15s;
            cursor: pointer;
        }}
        
        .card:hover {{
            transform: translateY(-2px);
            background: var(--bg-hover);
            border-color: var(--border-hover);
        }}
        
        .card-icon {{
            width: 48px;
            height: 48px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;
            background: var(--bg-elevated);
            flex-shrink: 0;
        }}
        
        .card-icon img {{
            width: 32px;
            height: 32px;
            object-fit: contain;
        }}
        
        .icon-letter {{
            width: 100%;
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1rem;
            font-weight: 500;
            color: var(--text-secondary);
            background: rgba(255, 255, 255, 0.04);
            border-radius: 12px;
        }}
        
        /* Card name - below icon */
        .card-name {{
            font-size: 0.8125rem;
            font-weight: 500;
            color: var(--text-secondary);
            text-align: center;
            max-width: 100%;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            line-height: 1.3;
        }}
        
        /* Hidden state for search filtering */
        .card.hidden,
        .category.hidden {{
            display: none;
        }}
        
        /* Footer */
        footer {{
            text-align: center;
            margin-top: 48px;
            padding-top: 16px;
            border-top: 1px solid var(--border-subtle);
            color: var(--text-muted);
            font-size: 0.625rem;
            letter-spacing: 0.02em;
        }}
        
        footer a {{
            color: var(--text-secondary);
            text-decoration: none;
            transition: color 0.15s;
        }}
        
        footer a:hover {{
            color: var(--text-primary);
        }}
        
        /* Responsive */
        @media (max-width: 768px) {{
            body {{
                padding: 16px 16px 48px;
            }}
            
            h1 {{
                font-size: 1.75rem;
            }}
            
            .search-wrapper {{
                max-width: 100%;
                margin-bottom: 24px;
            }}
            
            .cards-grid {{
                grid-template-columns: repeat(auto-fill, minmax(104px, 1fr));
                gap: 10px;
            }}
            
            .card {{
                padding: 16px 8px 12px;
            }}
            
            .card-icon {{
                width: 40px;
                height: 40px;
            }}
            
            .card-icon img {{
                width: 28px;
                height: 28px;
            }}
            
            .category {{
                margin-bottom: 20px;
            }}
        }}
        
        @media (min-width: 1400px) {{
            .cards-grid {{
                grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
            }}
        }}
        
        /* Smooth scrolling */
        html {{
            scroll-behavior: smooth;
        }}
        
        /* Selection color */
        ::selection {{
            background: rgba(139, 92, 246, 0.3);
            color: white;
        }}
        
        /* Scrollbar */
        ::-webkit-scrollbar {{
            width: 6px;
        }}
        
        ::-webkit-scrollbar-track {{
            background: transparent;
        }}
        
        ::-webkit-scrollbar-thumb {{
            background: rgba(255, 255, 255, 0.06);
            border-radius: 3px;
        }}
        
        ::-webkit-scrollbar-thumb:hover {{
            background: rgba(255, 255, 255, 0.1);
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>{self._escape_html(title)}</h1>
            <p class="subtitle">共 {data.total_count} 个书签 · 由 iTab Migration 生成</p>
        </header>
        
        <div class="search-wrapper">
            <svg class="search-icon" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clip-rule="evenodd"/>
            </svg>
            <input type="text" class="search-input" id="searchInput" placeholder="搜索书签、网站或关键词…" autocomplete="off">
            <span class="search-shortcut">Ctrl K</span>
        </div>
        <div class="search-results-count" id="searchResults"></div>
        
        <main id="bookmarksContainer">
            {"".join(category_sections)}
        </main>
        
        <footer>
            <p>Powered by <a href="https://github.com/user/itab-migration" target="_blank" rel="noopener">iTab Migration</a></p>
        </footer>
    </div>
    
    <script>
        // Search functionality
        const searchInput = document.getElementById('searchInput');
        const searchResults = document.getElementById('searchResults');
        const cards = document.querySelectorAll('.card');
        const categories = document.querySelectorAll('.category');
        
        searchInput.addEventListener('input', function() {{
            const query = this.value.toLowerCase().trim();
            let visibleCount = 0;
            
            if (query === '') {{
                cards.forEach(card => card.classList.remove('hidden'));
                categories.forEach(cat => cat.classList.remove('hidden'));
                searchResults.textContent = '';
                return;
            }}
            
            cards.forEach(card => {{
                const name = card.dataset.name || '';
                const matches = name.includes(query);
                card.classList.toggle('hidden', !matches);
                if (matches) visibleCount++;
            }});
            
            // Hide empty categories
            categories.forEach(cat => {{
                const visibleCards = cat.querySelectorAll('.card:not(.hidden)');
                cat.classList.toggle('hidden', visibleCards.length === 0);
            }});
            
            searchResults.textContent = visibleCount > 0 ? `找到 ${{visibleCount}} 个书签` : '未找到匹配的书签';
        }});
        
        // Keyboard shortcut: Cmd+K / Ctrl+K to focus search
        document.addEventListener('keydown', function(e) {{
            if ((e.metaKey || e.ctrlKey) && e.key === 'k') {{
                e.preventDefault();
                searchInput.focus();
                searchInput.select();
            }}
            if (e.key === 'Escape') {{
                searchInput.blur();
                searchInput.value = '';
                searchInput.dispatchEvent(new Event('input'));
            }}
        }});
        
        // Focus search on page load
        searchInput.focus();
    </script>
</body>
</html>'''
        
        # Write to file
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        logger.info(f"Generated portal HTML: {output_path}")
        return output_path
    
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
