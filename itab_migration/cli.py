"""
Command-line interface for iTab Migration Tool.

This module provides the CLI entry point for the migration tool.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import List, Optional

from . import __version__
from .migrator import MigrationConfig, migrate


def setup_logging(verbose: bool = False) -> None:
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    format_str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    logging.basicConfig(
        level=level,
        format=format_str,
        handlers=[
            logging.StreamHandler(sys.stdout),
        ]
    )


def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="itab-migration",
        description="Migrate iTab bookmarks and icons to Chrome browser",
        epilog=(
            "Examples:\n"
            "  %(prog)s backup.itabdata\n"
            "  %(prog)s backup.itabdata -o ./my_bookmarks\n"
            "  %(prog)s backup.itabdata --no-icons\n"
            "  %(prog)s -c config.json\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument(
        "input",
        type=str,
        nargs="?",
        help="Path to iTab backup file (.itabdata)",
    )
    
    parser.add_argument(
        "-o", "--output",
        type=str,
        default="./output",
        help="Output directory (default: ./output)",
    )
    
    parser.add_argument(
        "--no-icons",
        action="store_true",
        help="Skip downloading icons",
    )
    
    parser.add_argument(
        "--no-html",
        action="store_true",
        help="Skip generating HTML bookmarks",
    )
    
    parser.add_argument(
        "--no-json",
        action="store_true",
        help="Skip generating JSON bookmarks",
    )
    
    parser.add_argument(
        "--no-mapping",
        action="store_true",
        help="Skip generating icon mapping",
    )
    
    parser.add_argument(
        "--timeout",
        type=int,
        default=10,
        help="HTTP request timeout in seconds (default: 10)",
    )
    
    parser.add_argument(
        "--delay",
        type=float,
        default=0.1,
        help="Delay between downloads in seconds (default: 0.1)",
    )
    
    parser.add_argument(
        "-c", "--config",
        type=str,
        help="Path to configuration file (config.json)",
    )
    
    parser.add_argument(
        "--sync",
        action="store_true",
        help="Use synchronous downloader instead of async",
    )
    
    parser.add_argument(
        "--concurrency",
        type=int,
        default=10,
        help="Maximum concurrent downloads (default: 10)",
    )
    
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate bookmark URLs (check for broken links)",
    )
    
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate, don't migrate",
    )
    
    parser.add_argument(
        "--remove-invalid",
        action="store_true",
        help="Remove invalid bookmarks during validation",
    )
    
    parser.add_argument(
        "--export",
        type=str,
        help="Export format (chrome, firefox, edge, markdown, csv, json, opml)",
    )
    
    parser.add_argument(
        "--list-formats",
        action="store_true",
        help="List supported export formats",
    )
    
    parser.add_argument(
        "--clear-cache",
        action="store_true",
        help="Clear icon cache",
    )
    
    parser.add_argument(
        "--cache-stats",
        action="store_true",
        help="Show cache statistics",
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    
    parser.add_argument(
        "-V", "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    
    return parser.parse_args(args)


def main(args: Optional[List[str]] = None) -> int:
    """
    Main entry point for the CLI.
    
    Args:
        args: Command-line arguments (defaults to sys.argv)
        
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    parsed_args = parse_args(args)
    
    # Setup logging
    setup_logging(parsed_args.verbose)
    logger = logging.getLogger(__name__)
    
    try:
        # Handle utility commands first
        if parsed_args.list_formats:
            from .exporters import get_supported_formats
            formats = get_supported_formats()
            print("Supported export formats:")
            for fmt in formats:
                print(f"  - {fmt}")
            return 0
        
        if parsed_args.clear_cache:
            from .cache import IconCache, get_default_cache_dir
            cache = IconCache(get_default_cache_dir())
            count = cache.clear()
            print(f"Cleared {count} cached icons")
            return 0
        
        if parsed_args.cache_stats:
            from .cache import IconCache, get_default_cache_dir
            cache = IconCache(get_default_cache_dir())
            stats = cache.get_stats()
            print("Cache Statistics:")
            print(f"  Entries: {stats['entries']}")
            print(f"  Total size: {stats['total_size_mb']} MB")
            print(f"  Total accesses: {stats['total_accesses']}")
            print(f"  Cache directory: {stats['cache_dir']}")
            return 0
        
        # Load configuration
        from .config import Config
        
        if parsed_args.config:
            # Load from config file
            config = Config.load(parsed_args.config)
            # Override with command-line arguments
            if parsed_args.input:
                config.input_file = parsed_args.input
            if parsed_args.output != "./output":
                config.output_dir = parsed_args.output
        else:
            # Check if input is provided
            if not parsed_args.input:
                logger.error("Input file is required when not using config file")
                print("Error: Input file is required")
                print("Usage: itab-migration <backup.itabdata>")
                print("   or: itab-migration -c config.json")
                return 1
            
            # Create from command-line arguments
            config = Config(
                input_file=parsed_args.input,
                output_dir=parsed_args.output,
                download_icons=not parsed_args.no_icons,
                download_timeout=parsed_args.timeout,
                download_delay=parsed_args.delay,
                generate_html=not parsed_args.no_html,
                generate_json=not parsed_args.no_json,
                generate_mapping=not parsed_args.no_mapping,
                use_async=not parsed_args.sync,
                concurrency=parsed_args.concurrency,
                verbose=parsed_args.verbose,
            )
        
        # Parse backup file
        from .parser import ITABParser
        parser = ITABParser()
        data = parser.parse(config.input_file)
        
        logger.info(f"Found {data.total_count} bookmarks")
        
        # Validate bookmarks if requested
        if parsed_args.validate or parsed_args.validate_only:
            from .validator import validate_bookmarks_async
            
            print("\nValidating bookmarks...")
            report = validate_bookmarks_async(
                data.bookmarks,
                timeout=config.download_timeout,
                concurrency=config.concurrency,
                check_only=True,
                show_progress=True,
            )
            
            # Print validation report
            print("\n" + "=" * 50)
            print("Validation Report")
            print("=" * 50)
            print(f"Total: {report.total}")
            print(f"Valid: {report.valid}")
            print(f"Broken: {report.broken}")
            print(f"Redirects: {report.redirects}")
            print(f"Timeouts: {report.timeouts}")
            print(f"Errors: {report.errors}")
            
            if report.broken_bookmarks:
                print(f"\nBroken bookmarks:")
                for r in report.broken_bookmarks[:10]:
                    print(f"  - {r.bookmark.name}: {r.bookmark.url} ({r.error_message})")
                if len(report.broken_bookmarks) > 10:
                    print(f"  ... and {len(report.broken_bookmarks) - 10} more")
            
            if parsed_args.validate_only:
                return 0 if report.broken == 0 else 1
        
        # Export if requested
        if parsed_args.export:
            from .exporters import export_bookmarks
            
            output_path = Path(config.output_dir) / f"bookmarks.{parsed_args.export}"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            export_bookmarks(data, parsed_args.export, output_path)
            print(f"\nExported to: {output_path}")
            
            if not config.download_icons:
                return 0
        
        # Run migration
        logger.info(f"Starting migration: {config.input_file}")
        result = migrate(
            input_file=config.input_file,
            output_dir=config.output_dir,
            download_icons=config.download_icons,
        )
        
        # Print results
        if result.success:
            print("\n" + "=" * 50)
            print("Migration completed successfully!")
            print("=" * 50)
            print(f"Total bookmarks: {result.bookmarks_count}")
            print(f"Icons downloaded: {result.icons_downloaded}")
            print(f"Icons failed: {result.icons_failed}")
            print(f"\nGenerated files:")
            for file_type, file_path in result.generated_files.items():
                print(f"  - {file_type}: {file_path}")
            print("\n" + "=" * 50)
            return 0
        else:
            logger.error(f"Migration failed: {result.errors}")
            return 1
    
    except Exception as e:
        logger.error(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
