"""
Main migrator module.

This module provides the high-level interface for migrating iTab
bookmarks and icons to Chrome browser.
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, field

from .parser import ITABParser, ITABBackupData
from .downloader import IconDownloader, DownloadResult
from .bookmark_generator import BookmarkGenerator

logger = logging.getLogger(__name__)


@dataclass
class MigrationConfig:
    """Configuration for the migration process."""
    
    # Input settings
    input_file: str | Path = ""
    
    # Output settings
    output_dir: str | Path = "./output"
    
    # Download settings
    download_icons: bool = True
    download_timeout: int = 10
    download_delay: float = 0.1
    skip_existing_icons: bool = True
    
    # Async settings
    use_async: bool = True
    concurrency: int = 10
    
    # Generation settings
    generate_html: bool = True
    generate_json: bool = True
    generate_mapping: bool = True
    
    def validate(self) -> None:
        """Validate the configuration."""
        if not self.input_file:
            raise ValueError("Input file is required")
        
        input_path = Path(self.input_file)
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")
        
        if not input_path.suffix == ".itabdata":
            raise ValueError(f"Invalid file extension: {input_path.suffix}")


@dataclass
class MigrationResult:
    """Result of the migration process."""
    
    success: bool = True
    data: Optional[ITABBackupData] = None
    download_results: list = field(default_factory=list)
    generated_files: Dict[str, Path] = field(default_factory=dict)
    errors: list = field(default_factory=list)
    statistics: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def bookmarks_count(self) -> int:
        """Get total number of bookmarks."""
        return self.data.total_count if self.data else 0
    
    @property
    def icons_downloaded(self) -> int:
        """Get number of successfully downloaded icons."""
        return sum(1 for r in self.download_results if r.success)
    
    @property
    def icons_failed(self) -> int:
        """Get number of failed icon downloads."""
        return sum(1 for r in self.download_results if r.failed)


class ITabMigrator:
    """
    Main class for migrating iTab bookmarks to Chrome.
    
    This class orchestrates the entire migration process:
    1. Parse iTab backup file
    2. Download icons (optional)
    3. Generate Chrome bookmark files
    4. Generate icon mapping file
    
    Example:
        >>> from itab_migration import ITabMigrator, MigrationConfig
        >>> config = MigrationConfig(input_file="backup.itabdata")
        >>> migrator = ITabMigrator(config)
        >>> result = migrator.migrate()
        >>> print(f"Migrated {result.bookmarks_count} bookmarks")
    """
    
    def __init__(self, config: MigrationConfig):
        """
        Initialize the migrator.
        
        Args:
            config: Migration configuration
        """
        self.config = config
        self.parser = ITABParser()
        self.downloader: Optional[IconDownloader] = None
        self.generator = BookmarkGenerator()
    
    def migrate(self) -> MigrationResult:
        """
        Execute the migration process.
        
        Returns:
            MigrationResult with migration status and details
        """
        result = MigrationResult()
        
        try:
            # Validate configuration
            self.config.validate()
            
            # Setup output directory
            output_dir = Path(self.config.output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Step 1: Parse backup file
            logger.info(f"Parsing backup file: {self.config.input_file}")
            result.data = self.parser.parse(self.config.input_file)
            result.statistics = result.data.get_statistics()
            
            logger.info(
                f"Found {result.data.total_count} bookmarks "
                f"({len(result.data.bookmarks_with_icons)} with icons)"
            )
            
            # Step 2: Deduplicate bookmarks
            from .deduplicator import deduplicate_bookmarks, get_deduplication_stats
            original_bookmarks = result.data.bookmarks
            deduplicated, removed = deduplicate_bookmarks(original_bookmarks)
            
            if removed:
                stats = get_deduplication_stats(original_bookmarks, removed)
                logger.info(
                    f"Removed {stats['removed_count']} duplicate bookmarks "
                    f"({stats['duplicate_groups']} duplicate groups)"
                )
                result.data.bookmarks = deduplicated
            
            # Step 3: Download background image
            logger.info("Downloading background image...")
            self._download_background(output_dir)
            
            # Step 4: Download icons
            if self.config.download_icons:
                logger.info("Downloading icons...")
                result.download_results = self._download_icons(result.data, output_dir)
            
            # Step 5: Generate bookmark files
            logger.info("Generating bookmark files...")
            result.generated_files = self._generate_bookmarks(
                result.data,
                result.download_results,
                output_dir,
            )
            
            logger.info("Migration completed successfully")
            
        except Exception as e:
            result.success = False
            result.errors.append(str(e))
            logger.error(f"Migration failed: {e}")
        
        return result
    
    def _download_background(self, output_dir: Path) -> None:
        """Download background image for portal page."""
        import requests
        
        # Free background images from Unsplash (no API key required)
        background_urls = [
            "https://images.unsplash.com/photo-1519681393784-d120267933ba?w=1920&q=80",  # Mountain night
            "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=1920&q=80",  # Mountains
            "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=1920&q=80",  # Mountain sunset
            "https://images.unsplash.com/photo-1501785888041-af3ef285b470?w=1920&q=80",  # Landscape
        ]
        
        bg_path = output_dir / "background.jpg"
        
        # Skip if already exists
        if bg_path.exists():
            logger.info("Background image already exists")
            return
        
        for url in background_urls:
            try:
                logger.info(f"Downloading background image...")
                response = requests.get(url, timeout=30, stream=True)
                response.raise_for_status()
                
                with open(bg_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                logger.info(f"Background image saved: {bg_path}")
                return
                
            except Exception as e:
                logger.warning(f"Failed to download background: {e}")
                continue
        
        logger.warning("Could not download background image, using CSS gradient")
    
    def _download_icons(
        self,
        data: ITABBackupData,
        output_dir: Path,
    ) -> list:
        """Download icons for bookmarks."""
        icons_dir = output_dir / "icons"
        bookmarks_with_icons = data.bookmarks_with_icons
        
        if self.config.use_async:
            # Use async downloader
            from .async_downloader import download_icons_async
            results = download_icons_async(
                bookmarks=bookmarks_with_icons,
                output_dir=icons_dir,
                timeout=self.config.download_timeout,
                concurrency=self.config.concurrency,
                skip_existing=self.config.skip_existing_icons,
            )
            return results
        else:
            # Use synchronous downloader
            self.downloader = IconDownloader(
                output_dir=icons_dir,
                timeout=self.config.download_timeout,
                delay=self.config.download_delay,
            )
            
            try:
                results = self.downloader.download_all(
                    bookmarks_with_icons,
                    skip_existing=self.config.skip_existing_icons,
                )
                return results
            finally:
                self.downloader.cleanup()
    
    def _generate_bookmarks(
        self,
        data: ITABBackupData,
        download_results: list,
        output_dir: Path,
    ) -> Dict[str, Path]:
        """Generate bookmark files."""
        generated_files = {}
        
        # Generate HTML bookmarks (for Chrome import)
        if self.config.generate_html:
            html_path = output_dir / "chrome_bookmarks.html"
            self.generator.generate_html(data, html_path)
            generated_files["html"] = html_path
        
        # Generate beautiful portal HTML page
        icons_dir = output_dir / "icons"
        background_image = output_dir / "background.jpg"
        portal_path = output_dir / "index.html"
        self.generator.generate_portal_html(
            data, portal_path, icons_dir, 
            background_image=background_image if background_image.exists() else None
        )
        generated_files["portal"] = portal_path
        
        # Generate JSON bookmarks
        if self.config.generate_json:
            json_path = output_dir / "chrome_bookmarks.json"
            self.generator.generate_json(data, json_path)
            generated_files["json"] = json_path
        
        # Generate icon mapping
        if self.config.generate_mapping and download_results:
            mapping_path = output_dir / "icon_mapping.json"
            self.generator.generate_icon_mapping(data, download_results, mapping_path)
            generated_files["mapping"] = mapping_path
        
        return generated_files


def migrate(
    input_file: str | Path,
    output_dir: str | Path = "./output",
    download_icons: bool = True,
    **kwargs,
) -> MigrationResult:
    """
    Convenience function for migrating iTab bookmarks.
    
    Args:
        input_file: Path to iTab backup file (.itabdata)
        output_dir: Output directory for generated files
        download_icons: Whether to download icons
        **kwargs: Additional configuration options
        
    Returns:
        MigrationResult with migration status
        
    Example:
        >>> from itab_migration import migrate
        >>> result = migrate("backup.itabdata", "./output")
        >>> print(f"Migrated {result.bookmarks_count} bookmarks")
    """
    config = MigrationConfig(
        input_file=input_file,
        output_dir=output_dir,
        download_icons=download_icons,
        **kwargs,
    )
    
    migrator = ITabMigrator(config)
    return migrator.migrate()
