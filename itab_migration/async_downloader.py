"""
Async icon downloader module.

This module provides async functionality to download icons from URLs
with better performance using concurrent requests.
"""

import asyncio
import logging
from pathlib import Path
from typing import List, Optional, Tuple
from dataclasses import dataclass

import aiohttp
from tqdm import tqdm

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


class AsyncIconDownloader:
    """
    Async downloader for icons from bookmark URLs.
    
    This class handles downloading icons concurrently using asyncio
    and aiohttp for better performance.
    
    Example:
        >>> downloader = AsyncIconDownloader("./icons")
        >>> results = await downloader.download_all(bookmarks)
        >>> print(f"Downloaded {sum(r.success for r in results)} icons")
    """
    
    # Supported image extensions
    SUPPORTED_EXTENSIONS = {".svg", ".png", ".ico", ".jpg", ".jpeg", ".webp", ".gif"}
    
    # Default timeout for HTTP requests (seconds)
    DEFAULT_TIMEOUT = 10
    
    # Default concurrent requests
    DEFAULT_CONCURRENCY = 10
    
    def __init__(
        self,
        output_dir: str | Path,
        timeout: int = DEFAULT_TIMEOUT,
        concurrency: int = DEFAULT_CONCURRENCY,
    ):
        """
        Initialize the async icon downloader.
        
        Args:
            output_dir: Directory to save downloaded icons
            timeout: HTTP request timeout in seconds
            concurrency: Maximum concurrent requests
        """
        self.output_dir = Path(output_dir)
        self.timeout = timeout
        self.concurrency = concurrency
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_file_extension(self, url: str, content_type: Optional[str] = None) -> str:
        """
        Determine file extension from URL or content type.
        
        Args:
            url: The icon URL
            content_type: Optional HTTP content type header
            
        Returns:
            File extension including the dot (e.g., ".png")
        """
        from urllib.parse import urlparse
        
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
    
    async def _download_single(
        self,
        session: aiohttp.ClientSession,
        bookmark: BookmarkItem,
        semaphore: asyncio.Semaphore,
        pbar: tqdm,
    ) -> DownloadResult:
        """
        Download a single icon asynchronously.
        
        Args:
            session: aiohttp client session
            bookmark: Bookmark item to download
            semaphore: Semaphore for concurrency control
            pbar: Progress bar
            
        Returns:
            DownloadResult with download status
        """
        if not bookmark.has_icon:
            pbar.update(1)
            return DownloadResult(
                bookmark=bookmark,
                success=False,
                error_message="No icon URL available"
            )
        
        async with semaphore:
            try:
                async with session.get(
                    bookmark.icon_url,
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                ) as response:
                    if response.status != 200:
                        pbar.update(1)
                        return DownloadResult(
                            bookmark=bookmark,
                            success=False,
                            error_message=f"HTTP {response.status}"
                        )
                    
                    # Get content type
                    content_type = response.headers.get("Content-Type")
                    
                    # Determine file extension
                    extension = self._get_file_extension(bookmark.icon_url, content_type)
                    
                    # Generate filename
                    filename = self._generate_filename(bookmark, extension)
                    file_path = self.output_dir / filename
                    
                    # Read and save file
                    data = await response.read()
                    with open(file_path, "wb") as f:
                        f.write(data)
                    
                    pbar.update(1)
                    logger.debug(f"Downloaded: {bookmark.name}")
                    
                    return DownloadResult(
                        bookmark=bookmark,
                        success=True,
                        local_path=file_path,
                    )
                    
            except Exception as e:
                pbar.update(1)
                logger.debug(f"Failed to download {bookmark.name}: {e}")
                return DownloadResult(
                    bookmark=bookmark,
                    success=False,
                    error_message=str(e)
                )
    
    async def download_all(
        self,
        bookmarks: List[BookmarkItem],
        skip_existing: bool = True,
    ) -> List[DownloadResult]:
        """
        Download icons for multiple bookmarks asynchronously.
        
        Args:
            bookmarks: List of bookmark items
            skip_existing: Whether to skip already downloaded icons
            
        Returns:
            List of DownloadResult objects
        """
        # Filter bookmarks to download
        to_download = []
        skipped = []
        
        for bookmark in bookmarks:
            if not bookmark.has_icon:
                skipped.append(DownloadResult(
                    bookmark=bookmark,
                    success=False,
                    error_message="No icon URL available"
                ))
                continue
            
            # Check if already downloaded
            if skip_existing:
                existing_files = list(self.output_dir.glob(f"{bookmark.name}.*"))
                if not existing_files:
                    # Try with sanitized name
                    name = bookmark.name
                    for char in '<>:"/\\|?*':
                        name = name.replace(char, '_')
                    name = name.strip(' .')
                    existing_files = list(self.output_dir.glob(f"{name}.*"))
                
                if existing_files:
                    skipped.append(DownloadResult(
                        bookmark=bookmark,
                        success=True,
                        local_path=existing_files[0],
                    ))
                    continue
            
            to_download.append(bookmark)
        
        if not to_download:
            logger.info("All icons already downloaded")
            return skipped
        
        # Create progress bar
        pbar = tqdm(
            total=len(to_download),
            desc="Downloading icons",
            unit="icon",
            ncols=80,
        )
        
        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(self.concurrency)
        
        # Download concurrently
        async with aiohttp.ClientSession() as session:
            tasks = [
                self._download_single(session, bookmark, semaphore, pbar)
                for bookmark in to_download
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
        
        pbar.close()
        
        # Process results
        download_results = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Download task failed: {result}")
            else:
                download_results.append(result)
        
        # Combine with skipped
        all_results = skipped + download_results
        
        # Log summary
        successful = sum(1 for r in all_results if r.success)
        failed = sum(1 for r in all_results if r.failed)
        logger.info(f"Download complete: {successful} successful, {failed} failed")
        
        return all_results
    
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


def download_icons_async(
    bookmarks: List[BookmarkItem],
    output_dir: str | Path,
    timeout: int = 10,
    concurrency: int = 10,
    skip_existing: bool = True,
) -> List[DownloadResult]:
    """
    Convenience function for async icon downloading.
    
    Args:
        bookmarks: List of bookmark items
        output_dir: Directory to save icons
        timeout: HTTP request timeout
        concurrency: Maximum concurrent requests
        skip_existing: Whether to skip existing icons
        
    Returns:
        List of DownloadResult objects
    """
    downloader = AsyncIconDownloader(
        output_dir=output_dir,
        timeout=timeout,
        concurrency=concurrency,
    )
    
    return asyncio.run(downloader.download_all(bookmarks, skip_existing))
