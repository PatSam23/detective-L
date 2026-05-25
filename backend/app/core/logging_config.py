"""
Logging configuration for detective-L backend.

Sets up structured logging with both console and file handlers,
using daily rotation and detailed JSON formatting.
"""

import os
import json
import logging
import logging.handlers
from pathlib import Path
from datetime import datetime, timezone

# Create logs directory if it doesn't exist
# __file__ is app/core/logging_config.py, so parent.parent.parent goes to backend/
LOGS_DIR = Path(__file__).parent.parent.parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# Log file path
LOG_FILE = LOGS_DIR / f"detective-L_{datetime.now().strftime('%Y%m%d')}.log"

# Log format with timestamp, level, module, and message (for console)
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def format(self, record):
        log_record = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "lineno": record.lineno,
            "funcName": record.funcName,
        }
        
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
            
        # Add any extra attributes passed via 'extra='
        for key, value in record.__dict__.items():
            if key not in ['args', 'asctime', 'created', 'exc_info', 'exc_text', 'filename', 'funcName', 'levelname', 'levelno', 'lineno', 'module', 'msecs', 'message', 'msg', 'name', 'pathname', 'process', 'processName', 'relativeCreated', 'stack_info', 'thread', 'threadName']:
                log_record[key] = value
                
        return json.dumps(log_record)


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
    
    # Create formatters
    json_formatter = JSONFormatter()
    text_formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
    
    # File handler with rotation (always structured JSON)
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,  # Keep 5 backup files
    )
    file_handler.setLevel(logging.DEBUG)  # File gets all levels
    file_handler.setFormatter(json_formatter)
    root_logger.addHandler(file_handler)
    
    # Console handler
    if console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        # Use JSON for console if specified in environment, otherwise use text
        if os.getenv("LOG_FORMAT", "text").lower() == "json":
            console_handler.setFormatter(json_formatter)
        else:
            console_handler.setFormatter(text_formatter)
        root_logger.addHandler(console_handler)
    
    # Silence spammy third-party loggers
    logging.getLogger("watchfiles").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    
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
