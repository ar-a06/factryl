"""
Logging configuration for the Factryl system.
"""

import sys
from pathlib import Path
from loguru import logger

def setup_logging(config: dict) -> None:
    """
    Configure the logging system based on the provided configuration.
    
    Args:
        config: Dictionary containing logging configuration
    """
    # Remove default handler
    logger.remove()
    
    # Ensure log directory exists
    log_file = config.get('file', 'logs/factryl.log')
    log_dir = Path(log_file).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Add handlers
    # Console handler
    logger.add(
        sys.stderr,
        format=config.get('format', "{time} - {name} - {level} - {message}"),
        level=config.get('level', 'INFO'),
        colorize=True
    )
    
    # File handler
    logger.add(
        log_file,
        rotation=f"{config.get('max_size', 10*1024*1024)} B",  # Default 10MB
        retention=config.get('backup_count', 5),
        format=config.get('format', "{time} - {name} - {level} - {message}"),
        level=config.get('level', 'INFO'),
        compression="zip"
    )
    
    logger.info("Logging system initialized") 