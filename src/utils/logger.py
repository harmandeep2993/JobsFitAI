# src/utils/logger.py

"""
Central logging configuration for JobFitAI.

Usage in any module:
    from src.utils.logger import get_logger
    logger = get_logger(__name__)

    logger.info("Extraction complete — %d chars", len(text))
    logger.warning("Page %d empty", page_num)
    logger.error("Failed: %s", error)
    logger.debug("Raw JSON: %s", data)

Log output:
    Console  — INFO and above (coloured)
    File     — DEBUG and above (logs/jobfitai.log, rotating 5MB x 3 backups)

Log level controlled via config.yaml:
    logging:
      level: "DEBUG"   # DEBUG | INFO | WARNING | ERROR
"""

import logging
import logging.handlers
from pathlib import Path


# Config
LOG_DIR      = Path("logs")
LOG_FILE     = LOG_DIR / "jobfitai.log"
MAX_BYTES    = 5 * 1024 * 1024   # 5 MB per file
BACKUP_COUNT = 3                  # keep last 3 rotated files


# Formatters 
FILE_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)-30s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


class _ColourFormatter(logging.Formatter):
    
    """ Coloured console formatter. pplies ANSI colour codes per log level for readability.
    Falls back to plain text on terminals that don't support colour.
    """

    COLOURS = {
        logging.DEBUG:    "\033[36m",    # cyan
        logging.INFO:     "\033[32m",    # green
        logging.WARNING:  "\033[33m",    # amber
        logging.ERROR:    "\033[31m",    # red
        logging.CRITICAL: "\033[35m",    # magenta
    }
    RESET = "\033[0m"

    CONSOLE_FORMAT = "%(asctime)s | {colour}%(levelname)-8s%(reset)s | %(name)-30s | %(message)s"

    def format(self, record):
        colour = self.COLOURS.get(record.levelno, "")
        fmt = self.CONSOLE_FORMAT.format(colour=colour, reset=self.RESET)
        formatter = logging.Formatter(fmt, datefmt=DATE_FORMAT)
        return formatter.format(record)


# Setup

def _setup_logging(level: str = "DEBUG") -> None:
    """
    Configure root logger with console + rotating file handlers.
    Called once at startup. Subsequent calls are no-ops.

    Args:
        level (str): Log level — DEBUG | INFO | WARNING | ERROR
    """
    root = logging.getLogger()

    # Avoid duplicate handlers if called multiple times
    if root.handlers:
        return

    numeric_level = getattr(logging, level.upper(), logging.DEBUG)
    root.setLevel(logging.DEBUG)  # root captures everything — handlers filter

    #  Console handler
    console = logging.StreamHandler()
    console.setLevel(numeric_level)
    console.setFormatter(_ColourFormatter())
    root.addHandler(console)

    #  File handler (rotating)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    file_handler = logging.handlers.RotatingFileHandler(
        LOG_FILE,
        maxBytes    = MAX_BYTES,
        backupCount = BACKUP_COUNT,
        encoding    = "utf-8",
    )
    file_handler.setLevel(logging.DEBUG)   # always log everything to file
    file_handler.setFormatter(logging.Formatter(FILE_FORMAT, datefmt=DATE_FORMAT))
    root.addHandler(file_handler)


# Public API

def get_logger(name: str) -> logging.Logger:
    """
    Get a named logger for a module.
    Initialises logging on first call using config.yaml level if available.

    Args:
        name (str): Module name — pass __name__

    Returns:
        logging.Logger: Configured logger instance

    Example:
        logger = get_logger(__name__)
        logger.info("Starting extraction")
    """
    # Lazy init — read level from config if available
    if not logging.getLogger().handlers:
        level = "DEBUG"
        try:
            from src.utils.config import LOG_LEVEL
            level = LOG_LEVEL
        except Exception:
            pass  # config not yet loaded — use DEBUG default
        _setup_logging(level)

    # Shorten name for readability: src.parsers.pdf_parser → pdf_parser
    short_name = name.split(".")[-1] if "." in name else name
    return logging.getLogger(short_name)