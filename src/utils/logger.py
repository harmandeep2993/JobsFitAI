# src/utils/logger.py

"""
Central logging configuration for JobsFitAI.

Usage in any module:
    from src.utils.logger import get_logger
    logger = get_logger(__name__)

    logger.info("Extraction complete - %d chars", len(text))
    logger.warning("Page %d empty", page_num)
    logger.error("Failed: %s", error)
    logger.debug("Raw JSON: %s", data)

Log output:
    Console  - INFO and above (coloured)
    File     - DEBUG and above (logs/jobsfitai.log, rotating 5MB x 3 backups)

Log level controlled via config.yaml:
    logging:
      level: "DEBUG"   # DEBUG | INFO | WARNING | ERROR
"""

import logging
import logging.handlers
from pathlib import Path

LOG_DIR = Path("logs")
LOG_FILE = LOG_DIR / "jobsfitai.log"
MAX_BYTES = 5 * 1024 * 1024
BACKUP_COUNT = 3

FILE_FORMAT = "%(asctime)s | %(levelname)-7s | %(name)-15s | %(message)s"
DATE_FORMAT = "%H:%M:%S"

# Low-level helpers pinned to WARNING so their per-call detail stays out of
# normal runs. The major-event modules (resume_parser, resume, jd, matcher,
# job_matcher, app, ...) log clean one-line INFO summaries and are NOT muted.
# Set config logging.level to DEBUG to see all detail again.
_QUIET_INTERNAL = [
    "skills",
    "responsibilities",
    "experiences",
    "experience",
    "education",
    "languages",
    "certifications",
    "extract",
    "resume_prompt",
    "jd_prompt",
    "router",
    "embedding_model",
    "config",
    "validator",
    "pdf_parser",
    "docx_parser",
    "text_cleaner",
    "summary",
    "match_store",
]

# Module-level flag - survives re-imports in same process
_INITIALISED = False


class _ColourFormatter(logging.Formatter):
    """
    Coloured console formatter.
    Applies ANSI colour codes per log level for readability.
    """

    COLOURS = {
        logging.DEBUG: "\033[36m",
        logging.INFO: "\033[32m",
        logging.WARNING: "\033[33m",
        logging.ERROR: "\033[31m",
        logging.CRITICAL: "\033[35m",
    }
    RESET = "\033[0m"

    def format(self, record):
        """Apply ANSI colour to the level name before delegating to stdlib Formatter."""
        colour = self.COLOURS.get(record.levelno, "")
        reset = self.RESET
        fmt = (
            f"%(asctime)s | {colour}%(levelname)-7s{reset}"
            " | %(name)-15s | %(message)s"
        )
        formatter = logging.Formatter(fmt, datefmt=DATE_FORMAT)
        return formatter.format(record)


def _setup_logging(level: str = "DEBUG") -> None:
    """
    Configure root logger with console + rotating file handlers.
    Guarded by _INITIALISED flag - safe to call multiple times.

    Args:
        level (str): Log level - DEBUG | INFO | WARNING | ERROR
    """
    global _INITIALISED

    if _INITIALISED:
        return

    root = logging.getLogger()

    # Remove any handlers added by other libraries before us
    root.handlers.clear()

    numeric_level = getattr(logging, level.upper(), logging.DEBUG)
    root.setLevel(
        numeric_level
    )  # root level matches config - filters debug when INFO set

    # Console handler
    console = logging.StreamHandler()
    console.setLevel(numeric_level)
    console.setFormatter(_ColourFormatter())
    root.addHandler(console)

    # Rotating file handler
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    file_handler = logging.handlers.RotatingFileHandler(
        LOG_FILE,
        maxBytes=MAX_BYTES,
        backupCount=BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(FILE_FORMAT, datefmt=DATE_FORMAT))
    root.addHandler(file_handler)

    # Silence noisy third party loggers
    noisy_loggers = [
        "nicegui",
        "uvicorn",
        "uvicorn.access",
        "uvicorn.error",
        "fastapi",
        "httpx",
        "httpcore",
        "multipart",
        "sentence_transformers",
        "transformers",
        "torch",
        "PIL",
        "pdfplumber",
        "chromadb",
        "chromadb.telemetry",
        "pdfminer",
        "pdfminer.pdfpage",
        "pdfminer.pdfinterp",
        "pdfminer.pdfdocument",
        "pdfminer.pdfparser",
        "pdfminer.cmapdb",
        "pdfminer.encodingdb",
        "pdfminer.converter",
    ]
    for noisy in noisy_loggers:
        logging.getLogger(noisy).setLevel(logging.WARNING)

    # These warn even at WARNING (e.g. HF unauthenticated-request notice) - mute to ERROR.
    for q in ("huggingface_hub", "huggingface_hub.utils._http", "safetensors"):
        logging.getLogger(q).setLevel(logging.ERROR)

    # Pin chatty internal modules to WARNING so a run reads as a clean
    # high-level story (handled by job_matcher / app / relevance / etc.).
    # Skipped when the configured level is already DEBUG (full detail).
    if numeric_level > logging.DEBUG:
        for mod in _QUIET_INTERNAL:
            logging.getLogger(mod).setLevel(logging.WARNING)

    _INITIALISED = True


def get_logger(name: str) -> logging.Logger:
    """
    Get a named logger for a module.
    Initialises logging on first call - subsequent calls are instant.

    Args:
        name (str): Module name - pass __name__

    Returns:
        logging.Logger: Configured logger instance

    Example:
        logger = get_logger(__name__)
        logger.info("Starting extraction")
    """
    if not _INITIALISED:
        level = "DEBUG"
        try:
            from src.utils.config import LOG_LEVEL

            level = LOG_LEVEL
        except Exception:
            pass
        _setup_logging(level)

    # Shorten name: src.parsers.pdf_parser -> pdf_parser
    short_name = name.split(".")[-1] if "." in name else name
    return logging.getLogger(short_name)
