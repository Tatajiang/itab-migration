"""
Bookmark deduplication module.

This module provides functionality to remove duplicate bookmarks
based on URL or name similarity.
"""

import logging
from typing import List, Dict, Set, Tuple
from collections import defaultdict
from urllib.parse import urlparse, parse_qs, urlencode

from .parser import BookmarkItem

logger = logging.getLogger(__name__)


def normalize_url(url: str) -> str:
    """
    Normalize URL for comparison.
    
    Args:
        url: URL to normalize
        
    Returns:
        Normalized URL string
    """
    if not url:
        return ""
    
    # Parse URL
    parsed = urlparse(url.lower().strip())
    
    # Remove common prefixes
    netloc = parsed.netloc
    if netloc.startswith("www."):
        netloc = netloc[4:]
    
    # Remove trailing slash from path
    path = parsed.path.rstrip("/")
    if not path:
        path = "/"
    
    # Remove common tracking parameters
    if parsed.query:
        params = parse_qs(parsed.query)
        # Remove common tracking params
        tracking_params = {
            "utm_source", "utm_medium", "utm_campaign", 
            "utm_term", "utm_content", "ref", "source",
            "from", "fbclid", "gclid",
        }
        filtered_params = {
            k: v for k, v in params.items() 
            if k.lower() not in tracking_params
        }
        if filtered_params:
            query = urlencode(filtered_params, doseq=True)
        else:
            query = ""
    else:
        query = ""
    
    # Reconstruct URL
    normalized = f"{parsed.scheme}://{netloc}{path}"
    if query:
        normalized += f"?{query}"
    
    return normalized


def find_duplicates(bookmarks: List[BookmarkItem]) -> Dict[str, List[BookmarkItem]]:
    """
    Find duplicate bookmarks based on normalized URLs.
    
    Args:
        bookmarks: List of bookmark items
        
    Returns:
        Dictionary mapping normalized URL to list of duplicate bookmarks
    """
    url_groups: Dict[str, List[BookmarkItem]] = defaultdict(list)
    
    for bookmark in bookmarks:
        if bookmark.url:
            normalized = normalize_url(bookmark.url)
            url_groups[normalized].append(bookmark)
    
    # Filter to only groups with duplicates
    duplicates = {
        url: items for url, items in url_groups.items()
        if len(items) > 1
    }
    
    return duplicates


def deduplicate_bookmarks(
    bookmarks: List[BookmarkItem],
    keep_first: bool = True,
) -> Tuple[List[BookmarkItem], List[BookmarkItem]]:
    """
    Remove duplicate bookmarks.
    
    Args:
        bookmarks: List of bookmark items
        keep_first: If True, keep the first occurrence; otherwise keep the last
        
    Returns:
        Tuple of (deduplicated bookmarks, removed bookmarks)
    """
    seen_urls: Dict[str, int] = {}
    deduplicated = []
    removed = []
    
    for bookmark in bookmarks:
        if not bookmark.url:
            deduplicated.append(bookmark)
            continue
        
        normalized = normalize_url(bookmark.url)
        
        if normalized in seen_urls:
            if keep_first:
                # Keep first occurrence, remove this one
                removed.append(bookmark)
                logger.debug(f"Removed duplicate: {bookmark.name} ({bookmark.url})")
            else:
                # Keep this one, remove previous
                prev_index = seen_urls[normalized]
                removed.append(deduplicated[prev_index])
                deduplicated[prev_index] = bookmark
                seen_urls[normalized] = prev_index
                logger.debug(f"Replaced duplicate: {bookmark.name} ({bookmark.url})")
        else:
            seen_urls[normalized] = len(deduplicated)
            deduplicated.append(bookmark)
    
    return deduplicated, removed


def get_deduplication_stats(
    bookmarks: List[BookmarkItem],
    removed: List[BookmarkItem],
) -> Dict[str, any]:
    """
    Get statistics about deduplication.
    
    Args:
        bookmarks: Original bookmarks
        removed: Removed bookmarks
        
    Returns:
        Dictionary with deduplication statistics
    """
    # Find duplicate groups
    duplicates = find_duplicates(bookmarks)
    
    # Count by category
    removed_by_category = defaultdict(int)
    for bookmark in removed:
        removed_by_category[bookmark.category] += 1
    
    return {
        "original_count": len(bookmarks),
        "deduplicated_count": len(bookmarks) - len(removed),
        "removed_count": len(removed),
        "duplicate_groups": len(duplicates),
        "removed_by_category": dict(removed_by_category),
        "largest_duplicate_group": max(
            (len(items) for items in duplicates.values()),
            default=0
        ),
    }
