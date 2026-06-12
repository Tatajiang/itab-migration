"""
Icon downloader module.

This module provides functionality to download icons from URLs
and save them locally for use with Chrome bookmarks.
"""

import time
import logging
from pathlib import Path
from typing import List, Optional, Tuple
from dataclasses import dataclass
from urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .parser import BookmarkItem

logger = logging.getLogger(__name__)


@dataclass
class DownloadResult:
    """Represents the result of downloading an icon."""
    
    bookmark: BookmarkItem
    success: bool
    local_path: Optional[Path] = None
    error_message: Optional[str] = None
    
    @property
    def failed(self) -> bool:
        """Check if download failed."""
        return not self.success


class IconDownloader:
    """
    Downloads icons from bookmark URLs.
    
    This class handles downloading icons from various sources,
    with support for retries, rate limiting, and multiple formats.
    
    Example:
        >>> downloader = IconDownloader("./icons")
        >>> results = downloader.download_all(bookmarks)
        >>> print(f"Downloaded {sum(r.success for r in results)} icons")
    """
    
    # Supported image extensions
    SUPPORTED_EXTENSIONS = {".svg", ".png", ".ico", ".jpg", ".jpeg", ".webp", ".gif"}
    
    # Default timeout for HTTP requests (seconds)
    DEFAULT_TIMEOUT = 10
    
    # Default delay between requests (seconds)
    DEFAULT_DELAY = 0.1
    
    def __init__(
        self,
        output_dir: str | Path,
        timeout: int = DEFAULT_TIMEOUT,
        delay: float = DEFAULT_DELAY,
        max_retries: int = 3,
    ):
        """
        Initialize the icon downloader.
        
        Args:
            output_dir: Directory to save downloaded icons
            timeout: HTTP request timeout in seconds
            delay: Delay between requests in seconds
            max_retries: Maximum number of retry attempts
        """
        self.output_dir = Path(output_dir)
        self.timeout = timeout
        self.delay = delay
        self.max_retries = max_retries
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Configure session with retry strategy
        self.session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        """Create a requests session with retry strategy."""
        session = requests.Session()
        
        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=0.1,
            status_forcelist=[500, 502, 503, 504],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set user agent
        session.headers.update({
            "User-Agent": "iTab-Migration-Tool/1.0"
        })
        
        return session
    
    def _get_file_extension(self, url: str, content_type: Optional[str] = None) -> str:
        """
        Determine file extension from URL or content type.
        
        Args:
            url: The icon URL
            content_type: Optional HTTP content type header
            
        Returns:
            File extension including the dot (e.g., ".png")
        """
        # Try to get extension from URL
        parsed_url = urlparse(url)
        path = parsed_url.path
        
        if path:
            ext = Path(path).suffix.lower()
            if ext in self.SUPPORTED_EXTENSIONS:
                return ext
        
        # Try to determine from content type
        if content_type:
            content_type = content_type.lower()
            if "svg" in content_type:
                return ".svg"
            elif "png" in content_type:
                return ".png"
            elif "jpeg" in content_type or "jpg" in content_type:
                return ".jpg"
            elif "webp" in content_type:
                return ".webp"
            elif "gif" in content_type:
                return ".gif"
            elif "x-icon" in content_type or "ico" in content_type:
                return ".ico"
        
        # Default to .png
        return ".png"
    
    def _generate_filename(self, bookmark: BookmarkItem, extension: str) -> str:
        """
        Generate a filename for the downloaded icon.
        
        Args:
            bookmark: The bookmark item
            extension: File extension
            
        Returns:
            Filename string
        """
        # Use bookmark name as filename, sanitize for filesystem
        name = bookmark.name
        # Replace invalid characters with underscore
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            name = name.replace(char, '_')
        # Remove leading/trailing spaces and dots
        name = name.strip(' .')
        # Use ID as fallback if name is empty
        if not name:
            name = bookmark.id
        return f"{name}{extension}"
    
    def download_icon(self, bookmark: BookmarkItem) -> DownloadResult:
        """
        Download a single icon.
        
        Args:
            bookmark: Bookmark item with icon URL
            
        Returns:
            DownloadResult with download status
        """
        if not bookmark.has_icon:
            return DownloadResult(
                bookmark=bookmark,
                success=False,
                error_message="No icon URL available"
            )
        
        try:
            logger.info(f"Downloading icon for {bookmark.name}: {bookmark.icon_url}")
            
            response = self.session.get(
                bookmark.icon_url,
                timeout=self.timeout,
                stream=True,
            )
            response.raise_for_status()
            
            # Determine file extension
            content_type = response.headers.get("Content-Type")
            extension = self._get_file_extension(bookmark.icon_url, content_type)
            
            # Generate filename
            filename = self._generate_filename(bookmark, extension)
            file_path = self.output_dir / filename
            
            # Save file
            with open(file_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"Saved icon to {file_path}")
            
            return DownloadResult(
                bookmark=bookmark,
                success=True,
                local_path=file_path,
            )
            
        except requests.exceptions.RequestException as e:
            error_msg = f"HTTP error downloading {bookmark.icon_url}: {e}"
            logger.error(error_msg)
            return DownloadResult(
                bookmark=bookmark,
                success=False,
                error_message=error_msg,
            )
        
        except Exception as e:
            error_msg = f"Unexpected error downloading {bookmark.icon_url}: {e}"
            logger.error(error_msg)
            return DownloadResult(
                bookmark=bookmark,
                success=False,
                error_message=error_msg,
            )
    
    def download_all(
        self,
        bookmarks: List[BookmarkItem],
        skip_existing: bool = True,
    ) -> List[DownloadResult]:
        """
        Download icons for multiple bookmarks.
        
        Args:
            bookmarks: List of bookmark items
            skip_existing: Whether to skip already downloaded icons
            
        Returns:
            List of DownloadResult objects
        """
        results = []
        total = len(bookmarks)
        
        for i, bookmark in enumerate(bookmarks, 1):
            if not bookmark.has_icon:
                logger.debug(f"[{i}/{total}] Skipping {bookmark.name} - no icon URL")
                results.append(DownloadResult(
                    bookmark=bookmark,
                    success=False,
                    error_message="No icon URL available"
                ))
                continue
            
            # Check if already downloaded
            if skip_existing:
                existing_files = list(self.output_dir.glob(f"{bookmark.id}.*"))
                if existing_files:
                    logger.info(f"[{i}/{total}] Already exists: {bookmark.name}")
                    results.append(DownloadResult(
                        bookmark=bookmark,
                        success=True,
                        local_path=existing_files[0],
                    ))
                    continue
            
            logger.info(f"[{i}/{total}] Downloading: {bookmark.name}")
            result = self.download_icon(bookmark)
            results.append(result)
            
            # Rate limiting
            if i < total and self.delay > 0:
                time.sleep(self.delay)
        
        # Log summary
        successful = sum(1 for r in results if r.success)
        failed = sum(1 for r in results if r.failed)
        logger.info(f"Download complete: {successful} successful, {failed} failed")
        
        return results
    
    def get_downloaded_icons(self) -> List[Path]:
        """
        Get list of all downloaded icon files.
        
        Returns:
            List of paths to downloaded icon files
        """
        icons = []
        for ext in self.SUPPORTED_EXTENSIONS:
            icons.extend(self.output_dir.glob(f"*{ext}"))
        return sorted(icons)
    
    def cleanup(self):
        """Clean up the HTTP session."""
        self.session.close()
