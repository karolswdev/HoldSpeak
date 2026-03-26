"""Logging configuration for HoldSpeak."""

import logging
import sys
from pathlib import Path

LOG_DIR = Path.home() / ".local" / "share" / "holdspeak"
LOG_FILE = LOG_DIR / "holdspeak.log"


def setup_logging(verbose: bool = False) -> logging.Logger:
    """Configure logging for HoldSpeak.
    
    Logs to both file and stderr (if verbose).
    """
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    logger = logging.getLogger("holdspeak")
    logger.setLevel(logging.DEBUG)
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # File handler - always logs everything
    file_handler = logging.FileHandler(LOG_FILE, mode='a')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # Console handler - only if verbose
    if verbose:
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(logging.DEBUG)
        console_formatter = logging.Formatter('%(levelname)-8s | %(message)s')
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a child logger for a module."""
    return logging.getLogger(f"holdspeak.{name}")
