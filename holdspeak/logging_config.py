"""Logging configuration for HoldSpeak."""

import logging
import sys
from pathlib import Path

LOG_DIR = Path.home() / ".local" / "share" / "holdspeak"
LOG_FILE = LOG_DIR / "holdspeak.log"


class RedactingFormatter(logging.Formatter):
    """A log line, its traceback included, with no credential in it
    (PHILO-17 redact): a provider's stderr or error body can echo a token.
    The scan reads at most 64k characters; the rest is cut with a marker."""

    def format(self, record: logging.LogRecord) -> str:
        from .redaction import redact_bounded

        return redact_bounded(super().format(record))


class RedactingFilter(logging.Filter):
    """The same redaction for a logger whose handlers HoldSpeak does not own
    (uvicorn's, under ``log_config=None``): the message is rendered and
    redacted, and the traceback is rendered and redacted into ``exc_text``,
    which every Formatter prints as it is."""

    def filter(self, record: logging.LogRecord) -> bool:
        from .redaction import redact_bounded

        try:
            record.msg = redact_bounded(record.getMessage())
            record.args = None
            if record.exc_info and not record.exc_text:
                record.exc_text = redact_bounded(logging.Formatter().formatException(record.exc_info))
            elif record.exc_text:
                record.exc_text = redact_bounded(record.exc_text)
            if record.stack_info:
                record.stack_info = redact_bounded(record.stack_info)
        except Exception:  # a log line never breaks the caller
            pass
        return True


#: Loggers whose records HoldSpeak's handlers never format.
_FOREIGN_LOGGERS = ("uvicorn", "uvicorn.error", "uvicorn.access", "uvicorn.asgi")
_FILTER = RedactingFilter()


def install_log_redaction() -> None:
    """Put the redacting filter on uvicorn's loggers and on every root
    handler (PHILO-17 redact, Astra r1 MUST 3). The hub calls it before it
    starts uvicorn with ``log_config=None``. Safe to call twice."""
    for name in _FOREIGN_LOGGERS:
        target = logging.getLogger(name)
        if _FILTER not in target.filters:
            target.addFilter(_FILTER)
    for handler in logging.getLogger().handlers:
        if _FILTER not in handler.filters:
            handler.addFilter(_FILTER)


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
    file_formatter = RedactingFormatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # Console handler - only if verbose
    if verbose:
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(logging.DEBUG)
        console_formatter = RedactingFormatter('%(levelname)-8s | %(message)s')
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a child logger for a module."""
    return logging.getLogger(f"holdspeak.{name}")
