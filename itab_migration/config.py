"""
Configuration file support module.

This module provides functionality to load and save configuration
from JSON files.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)


@dataclass
class Config:
    """Configuration dataclass for iTab Migration Tool."""
    
    # Input settings
    input_file: str = ""
    
    # Output settings
    output_dir: str = "./output"
    
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
    generate_portal: bool = True
    
    # Background settings
    download_background: bool = True
    
    # Display settings
    show_progress: bool = True
    verbose: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Config':
        """Create config from dictionary."""
        # Filter out unknown keys
        valid_keys = {f.name for f in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered_data)
    
    def save(self, file_path: str | Path) -> None:
        """
        Save configuration to JSON file.
        
        Args:
            file_path: Path to save configuration
        """
        file_path = Path(file_path)
        
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
        
        logger.info(f"Configuration saved to {file_path}")
    
    @classmethod
    def load(cls, file_path: str | Path) -> 'Config':
        """
        Load configuration from JSON file.
        
        Args:
            file_path: Path to configuration file
            
        Returns:
            Config object
            
        Raises:
            FileNotFoundError: If file does not exist
            json.JSONDecodeError: If file is not valid JSON
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")
        
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        config = cls.from_dict(data)
        logger.info(f"Configuration loaded from {file_path}")
        
        return config
    
    @classmethod
    def load_or_default(cls, file_path: str | Path) -> 'Config':
        """
        Load configuration from file, or return default if not found.
        
        Args:
            file_path: Path to configuration file
            
        Returns:
            Config object
        """
        try:
            return cls.load(file_path)
        except FileNotFoundError:
            logger.info(f"Configuration file not found, using defaults")
            return cls()
    
    def validate(self) -> None:
        """Validate the configuration."""
        if not self.input_file:
            raise ValueError("Input file is required")
        
        input_path = Path(self.input_file)
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")
        
        if not input_path.suffix == ".itabdata":
            raise ValueError(f"Invalid file extension: {input_path.suffix}")
        
        if self.concurrency < 1:
            raise ValueError("Concurrency must be at least 1")
        
        if self.download_timeout < 1:
            raise ValueError("Download timeout must be at least 1 second")


def create_default_config(input_file: str, output_dir: str = "./output") -> Config:
    """
    Create a default configuration with specified input and output.
    
    Args:
        input_file: Path to iTab backup file
        output_dir: Output directory
        
    Returns:
        Config object with defaults
    """
    return Config(
        input_file=input_file,
        output_dir=output_dir,
    )
