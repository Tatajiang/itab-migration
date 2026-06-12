"""
Icon caching module.

This module provides a local cache system for downloaded icons
to avoid redundant downloads and improve performance.
"""

import hashlib
import json
import logging
import sqlite3
import time
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class IconCache:
    """
    Local icon cache using SQLite database.
    
    Caches downloaded icons based on URL hash to avoid
    redundant downloads.
    
    Example:
        >>> cache = IconCache("~/.itab-migration/cache")
        >>> cache.set("https://example.com/icon.png", "/path/to/icon.png")
        >>> path = cache.get("https://example.com/icon.png")
    """
    
    def __init__(
        self,
        cache_dir: str | Path,
        max_age_days: int = 30,
    ):
        """
        Initialize the icon cache.
        
        Args:
            cache_dir: Directory to store cache
            max_age_days: Maximum age of cache entries in days
        """
        self.cache_dir = Path(cache_dir).expanduser()
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.db_path = self.cache_dir / "cache.db"
        self.icons_dir = self.cache_dir / "icons"
        self.icons_dir.mkdir(exist_ok=True)
        
        self.max_age_days = max_age_days
        
        # Initialize database
        self._init_db()
    
    def _init_db(self) -> None:
        """Initialize the SQLite database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS icon_cache (
                    url_hash TEXT PRIMARY KEY,
                    url TEXT NOT NULL,
                    local_path TEXT NOT NULL,
                    file_size INTEGER,
                    created_at REAL,
                    last_accessed REAL,
                    access_count INTEGER DEFAULT 0
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_url_hash 
                ON icon_cache(url_hash)
            """)
            conn.commit()
    
    def _hash_url(self, url: str) -> str:
        """
        Generate hash for URL.
        
        Args:
            url: URL to hash
            
        Returns:
            SHA256 hash of URL
        """
        return hashlib.sha256(url.encode()).hexdigest()[:16]
    
    def get(self, url: str) -> Optional[Path]:
        """
        Get cached icon path for URL.
        
        Args:
            url: Icon URL
            
        Returns:
            Path to cached icon, or None if not cached
        """
        url_hash = self._hash_url(url)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT local_path, created_at FROM icon_cache WHERE url_hash = ?",
                (url_hash,)
            )
            row = cursor.fetchone()
            
            if row is None:
                return None
            
            local_path, created_at = row
            
            # Check if cache entry is expired
            if self.max_age_days > 0:
                max_age = timedelta(days=self.max_age_days)
                if datetime.now() - datetime.fromtimestamp(created_at) > max_age:
                    logger.debug(f"Cache expired for {url}")
                    self._remove(url_hash)
                    return None
            
            # Check if file exists
            icon_path = Path(local_path)
            if not icon_path.exists():
                logger.debug(f"Cached file not found: {local_path}")
                self._remove(url_hash)
                return None
            
            # Update access time
            conn.execute(
                "UPDATE icon_cache SET last_accessed = ?, access_count = access_count + 1 WHERE url_hash = ?",
                (time.time(), url_hash)
            )
            conn.commit()
            
            logger.debug(f"Cache hit for {url}")
            return icon_path
    
    def set(self, url: str, local_path: Path) -> None:
        """
        Cache an icon.
        
        Args:
            url: Icon URL
            local_path: Path to downloaded icon
        """
        url_hash = self._hash_url(url)
        local_path = Path(local_path)
        
        if not local_path.exists():
            logger.warning(f"Cannot cache non-existent file: {local_path}")
            return
        
        file_size = local_path.stat().st_size
        now = time.time()
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT OR REPLACE INTO icon_cache 
                   (url_hash, url, local_path, file_size, created_at, last_accessed, access_count)
                   VALUES (?, ?, ?, ?, ?, ?, 0)""",
                (url_hash, url, str(local_path), file_size, now, now)
            )
            conn.commit()
        
        logger.debug(f"Cached icon: {url} -> {local_path}")
    
    def _remove(self, url_hash: str) -> None:
        """Remove a cache entry."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM icon_cache WHERE url_hash = ?", (url_hash,))
            conn.commit()
    
    def remove(self, url: str) -> bool:
        """
        Remove a cached icon.
        
        Args:
            url: Icon URL
            
        Returns:
            True if removed, False if not found
        """
        url_hash = self._hash_url(url)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT local_path FROM icon_cache WHERE url_hash = ?",
                (url_hash,)
            )
            row = cursor.fetchone()
            
            if row is None:
                return False
            
            # Remove file
            icon_path = Path(row[0])
            if icon_path.exists():
                icon_path.unlink()
            
            # Remove from database
            self._remove(url_hash)
            
            logger.debug(f"Removed cached icon: {url}")
            return True
    
    def clear(self) -> int:
        """
        Clear all cached icons.
        
        Returns:
            Number of entries cleared
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM icon_cache")
            count = cursor.fetchone()[0]
            
            # Remove all icon files
            for icon_file in self.icons_dir.iterdir():
                if icon_file.is_file():
                    icon_file.unlink()
            
            # Clear database
            conn.execute("DELETE FROM icon_cache")
            conn.commit()
        
        logger.info(f"Cleared {count} cached icons")
        return count
    
    def cleanup(self) -> int:
        """
        Remove expired cache entries.
        
        Returns:
            Number of entries removed
        """
        if self.max_age_days <= 0:
            return 0
        
        max_age = timedelta(days=self.max_age_days)
        cutoff = (datetime.now() - max_age).timestamp()
        
        with sqlite3.connect(self.db_path) as conn:
            # Find expired entries
            cursor = conn.execute(
                "SELECT url_hash, local_path FROM icon_cache WHERE created_at < ?",
                (cutoff,)
            )
            expired = cursor.fetchall()
            
            # Remove expired files
            for url_hash, local_path in expired:
                icon_path = Path(local_path)
                if icon_path.exists():
                    icon_path.unlink()
            
            # Remove from database
            conn.execute("DELETE FROM icon_cache WHERE created_at < ?", (cutoff,))
            conn.commit()
        
        if expired:
            logger.info(f"Cleaned up {len(expired)} expired cache entries")
        
        return len(expired)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT COUNT(*), SUM(file_size), SUM(access_count) FROM icon_cache"
            )
            count, total_size, total_accesses = cursor.fetchone()
            
            total_size = total_size or 0
            total_accesses = total_accesses or 0
        
        return {
            "entries": count,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "total_accesses": total_accesses,
            "cache_dir": str(self.cache_dir),
        }
    
    def has(self, url: str) -> bool:
        """
        Check if URL is cached.
        
        Args:
            url: Icon URL
            
        Returns:
            True if cached, False otherwise
        """
        return self.get(url) is not None


def get_default_cache_dir() -> Path:
    """Get the default cache directory."""
    return Path.home() / ".itab-migration" / "cache"
