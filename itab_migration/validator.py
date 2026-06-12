"""
Bookmark validation module.

This module provides async functionality to validate bookmark URLs
and detect broken links or redirects.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

import aiohttp
from tqdm import tqdm

from .parser import BookmarkItem

logger = logging.getLogger(__name__)


class ValidationStatus(str, Enum):
    """Status of bookmark validation."""
    VALID = "valid"
    BROKEN = "broken"
    REDIRECT = "redirect"
    TIMEOUT = "timeout"
    ERROR = "error"
    SKIPPED = "skipped"


@dataclass
class ValidationResult:
    """Result of validating a single bookmark."""
    
    bookmark: BookmarkItem
    status: ValidationStatus
    status_code: Optional[int] = None
    final_url: Optional[str] = None
    redirect_count: int = 0
    response_time: Optional[float] = None
    error_message: Optional[str] = None
    
    @property
    def is_valid(self) -> bool:
        """Check if bookmark is valid."""
        return self.status == ValidationStatus.VALID
    
    @property
    def is_broken(self) -> bool:
        """Check if bookmark is broken."""
        return self.status == ValidationStatus.BROKEN
    
    @property
    def has_redirect(self) -> bool:
        """Check if bookmark has redirect."""
        return self.status == ValidationStatus.REDIRECT


@dataclass
class ValidationReport:
    """Report of bookmark validation."""
    
    total: int = 0
    valid: int = 0
    broken: int = 0
    redirects: int = 0
    timeouts: int = 0
    errors: int = 0
    skipped: int = 0
    results: List[ValidationResult] = field(default_factory=list)
    
    @property
    def broken_bookmarks(self) -> List[ValidationResult]:
        """Get list of broken bookmarks."""
        return [r for r in self.results if r.is_broken]
    
    @property
    def redirect_bookmarks(self) -> List[ValidationResult]:
        """Get list of bookmarks with redirects."""
        return [r for r in self.results if r.has_redirect]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary."""
        return {
            "total": self.total,
            "valid": self.valid,
            "broken": self.broken,
            "redirects": self.redirects,
            "timeouts": self.timeouts,
            "errors": self.errors,
            "skipped": self.skipped,
            "broken_bookmarks": [
                {
                    "name": r.bookmark.name,
                    "url": r.bookmark.url,
                    "status_code": r.status_code,
                    "error": r.error_message,
                }
                for r in self.broken_bookmarks
            ],
            "redirect_bookmarks": [
                {
                    "name": r.bookmark.name,
                    "url": r.bookmark.url,
                    "final_url": r.final_url,
                    "redirect_count": r.redirect_count,
                }
                for r in self.redirect_bookmarks
            ],
        }


class AsyncBookmarkValidator:
    """
    Async validator for bookmark URLs.
    
    This class validates bookmarks concurrently using asyncio
    and aiohttp for better performance.
    
    Example:
        >>> validator = AsyncBookmarkValidator()
        >>> report = await validator.validate_all(bookmarks)
        >>> print(f"Found {report.broken} broken bookmarks")
    """
    
    # Default timeout for HTTP requests (seconds)
    DEFAULT_TIMEOUT = 10
    
    # Default concurrent requests
    DEFAULT_CONCURRENCY = 20
    
    # Default max redirects
    DEFAULT_MAX_REDIRECTS = 5
    
    def __init__(
        self,
        timeout: int = DEFAULT_TIMEOUT,
        concurrency: int = DEFAULT_CONCURRENCY,
        max_redirects: int = DEFAULT_MAX_REDIRECTS,
        follow_redirects: bool = True,
        check_only: bool = False,
    ):
        """
        Initialize the async bookmark validator.
        
        Args:
            timeout: HTTP request timeout in seconds
            concurrency: Maximum concurrent requests
            max_redirects: Maximum number of redirects to follow
            follow_redirects: Whether to follow redirects
            check_only: If True, only check status code (faster)
        """
        self.timeout = timeout
        self.concurrency = concurrency
        self.max_redirects = max_redirects
        self.follow_redirects = follow_redirects
        self.check_only = check_only
    
    async def _validate_single(
        self,
        session: aiohttp.ClientSession,
        bookmark: BookmarkItem,
        semaphore: asyncio.Semaphore,
        pbar: tqdm,
    ) -> ValidationResult:
        """
        Validate a single bookmark asynchronously.
        
        Args:
            session: aiohttp client session
            bookmark: Bookmark item to validate
            semaphore: Semaphore for concurrency control
            pbar: Progress bar
            
        Returns:
            ValidationResult with validation status
        """
        if not bookmark.url:
            pbar.update(1)
            return ValidationResult(
                bookmark=bookmark,
                status=ValidationStatus.SKIPPED,
                error_message="No URL"
            )
        
        # Skip non-HTTP URLs
        if not bookmark.url.startswith(("http://", "https://")):
            pbar.update(1)
            return ValidationResult(
                bookmark=bookmark,
                status=ValidationStatus.SKIPPED,
                error_message="Non-HTTP URL"
            )
        
        async with semaphore:
            import time
            start_time = time.time()
            
            try:
                if self.check_only:
                    # HEAD request (faster)
                    async with session.head(
                        bookmark.url,
                        timeout=aiohttp.ClientTimeout(total=self.timeout),
                        allow_redirects=self.follow_redirects,
                        ssl=False,
                    ) as response:
                        response_time = time.time() - start_time
                        
                        if response.status >= 400:
                            pbar.update(1)
                            return ValidationResult(
                                bookmark=bookmark,
                                status=ValidationStatus.BROKEN,
                                status_code=response.status,
                                response_time=response_time,
                                error_message=f"HTTP {response.status}",
                            )
                        
                        # Check for redirect
                        if response.history:
                            pbar.update(1)
                            return ValidationResult(
                                bookmark=bookmark,
                                status=ValidationStatus.REDIRECT,
                                status_code=response.status,
                                final_url=str(response.url),
                                redirect_count=len(response.history),
                                response_time=response_time,
                            )
                        
                        pbar.update(1)
                        return ValidationResult(
                            bookmark=bookmark,
                            status=ValidationStatus.VALID,
                            status_code=response.status,
                            response_time=response_time,
                        )
                else:
                    # GET request (more accurate)
                    async with session.get(
                        bookmark.url,
                        timeout=aiohttp.ClientTimeout(total=self.timeout),
                        allow_redirects=self.follow_redirects,
                        ssl=False,
                    ) as response:
                        response_time = time.time() - start_time
                        
                        if response.status >= 400:
                            pbar.update(1)
                            return ValidationResult(
                                bookmark=bookmark,
                                status=ValidationStatus.BROKEN,
                                status_code=response.status,
                                response_time=response_time,
                                error_message=f"HTTP {response.status}",
                            )
                        
                        # Check for redirect
                        if response.history:
                            pbar.update(1)
                            return ValidationResult(
                                bookmark=bookmark,
                                status=ValidationStatus.REDIRECT,
                                status_code=response.status,
                                final_url=str(response.url),
                                redirect_count=len(response.history),
                                response_time=response_time,
                            )
                        
                        pbar.update(1)
                        return ValidationResult(
                            bookmark=bookmark,
                            status=ValidationStatus.VALID,
                            status_code=response.status,
                            response_time=response_time,
                        )
                    
            except asyncio.TimeoutError:
                pbar.update(1)
                return ValidationResult(
                    bookmark=bookmark,
                    status=ValidationStatus.TIMEOUT,
                    response_time=self.timeout,
                    error_message="Request timeout",
                )
            except aiohttp.ClientError as e:
                pbar.update(1)
                return ValidationResult(
                    bookmark=bookmark,
                    status=ValidationStatus.ERROR,
                    response_time=time.time() - start_time,
                    error_message=str(e),
                )
            except Exception as e:
                pbar.update(1)
                return ValidationResult(
                    bookmark=bookmark,
                    status=ValidationStatus.ERROR,
                    response_time=time.time() - start_time,
                    error_message=str(e),
                )
    
    async def validate_all(
        self,
        bookmarks: List[BookmarkItem],
        show_progress: bool = True,
    ) -> ValidationReport:
        """
        Validate all bookmarks asynchronously.
        
        Args:
            bookmarks: List of bookmark items to validate
            show_progress: Whether to show progress bar
            
        Returns:
            ValidationReport with validation results
        """
        if not bookmarks:
            return ValidationReport()
        
        # Create progress bar
        pbar = tqdm(
            total=len(bookmarks),
            desc="Validating bookmarks",
            unit="url",
            ncols=80,
            disable=not show_progress,
        )
        
        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(self.concurrency)
        
        # Configure session
        connector = aiohttp.TCPConnector(
            limit=self.concurrency,
            force_close=True,
            enable_cleanup_closed=True,
        )
        
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        
        # Validate concurrently
        async with aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
        ) as session:
            tasks = [
                self._validate_single(session, bookmark, semaphore, pbar)
                for bookmark in bookmarks
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
        
        pbar.close()
        
        # Build report
        report = ValidationReport()
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Validation task failed: {result}")
                report.errors += 1
            else:
                report.results.append(result)
                report.total += 1
                
                if result.status == ValidationStatus.VALID:
                    report.valid += 1
                elif result.status == ValidationStatus.BROKEN:
                    report.broken += 1
                elif result.status == ValidationStatus.REDIRECT:
                    report.redirects += 1
                elif result.status == ValidationStatus.TIMEOUT:
                    report.timeouts += 1
                elif result.status == ValidationStatus.ERROR:
                    report.errors += 1
                elif result.status == ValidationStatus.SKIPPED:
                    report.skipped += 1
        
        # Log summary
        logger.info(
            f"Validation complete: {report.valid} valid, "
            f"{report.broken} broken, {report.redirects} redirects, "
            f"{report.timeouts} timeouts, {report.errors} errors"
        )
        
        return report


def validate_bookmarks_async(
    bookmarks: List[BookmarkItem],
    timeout: int = 10,
    concurrency: int = 20,
    check_only: bool = True,
    show_progress: bool = True,
) -> ValidationReport:
    """
    Convenience function for async bookmark validation.
    
    Args:
        bookmarks: List of bookmark items
        timeout: HTTP request timeout
        concurrency: Maximum concurrent requests
        check_only: If True, only check status code (faster)
        show_progress: Whether to show progress bar
        
    Returns:
        ValidationReport with validation results
    """
    validator = AsyncBookmarkValidator(
        timeout=timeout,
        concurrency=concurrency,
        check_only=check_only,
    )
    
    return asyncio.run(validator.validate_all(bookmarks, show_progress))
