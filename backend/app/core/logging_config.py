"""
Logging configuration for detective-L backend.

Sets up structured logging with both console and file handlers,
using daily rotation and detailed formatting.
"""

import os
import logging
import logging.handlers
from pathlib import Path
from datetime import datetime

# Create logs directory if it doesn't exist
# __file__ is app/core/logging_config.py, so parent.parent.parent goes to backend/
LOGS_DIR = Path(__file__).parent.parent.parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# Log file path
LOG_FILE = LOGS_DIR / f"detective-L_{datetime.now().strftime('%Y%m%d')}.log"

# Log format with timestamp, level, module, and message
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(
    level: int = logging.INFO,
    log_file: str = None,
    console: bool = True,
) -> logging.Logger:
    """
    Configure logging with file and console handlers.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (uses default if None)
        console: Whether to also log to console
    
    Returns:
        Configured root logger
    """
    if log_file is None:
        log_file = str(LOG_FILE)
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create formatter
    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,  # Keep 5 backup files
    )
    file_handler.setLevel(logging.DEBUG)  # File gets all levels
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    # Console handler
    if console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.
    
    Args:
        name: Module name (typically __name__)
    
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


# Initialize on module import
setup_logging(level=logging.INFO, console=True)
