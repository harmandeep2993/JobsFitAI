# src/matcher/embedding_model.py

"""
Sentence-transformers embedding model loader.
Loads the model once and reuses it across the application.
"""

import contextlib
import os
from pathlib import Path

# Quiet HuggingFace/transformers noise before they're imported below
# (progress bars, advisory warnings, the model "LOAD REPORT").
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")
os.environ.setdefault("TRANSFORMERS_NO_ADVISORY_WARNINGS", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
# TQDM_DISABLE is checked by tqdm per-instance at __init__ time (not import time),
# so setting it here silences all progress bars for this process.
os.environ["TQDM_DISABLE"] = "1"

from sentence_transformers import SentenceTransformer

try:
    from transformers.utils import logging as _hf_logging

    _hf_logging.set_verbosity_error()
except Exception:
    pass

from src.utils import get_logger

logger = get_logger(__name__)

# Multilingual model - supports 50+ languages including all European languages
MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
MODEL_SHORT = MODEL_NAME.split("/")[-1]

# Local cache inside the project - loaded directly without any HF Hub lookup.
# Falls back to downloading from HuggingFace on first run, then saves here.
MODEL_DIR = Path(__file__).parent.parent.parent / "data" / "models" / MODEL_SHORT

_model = None


@contextlib.contextmanager
def _suppress_native_output():
    """
    Silence the tqdm weights bar and any native prints during model load.

    Best-effort: redirect fd 1 & 2 to devnull to silence any remaining
    native prints. tqdm is already disabled globally via TQDM_DISABLE=1 set
    at module import. Catches OSError silently (e.g. WinError 1 on Windows
    threadpools) and skips fd suppression without aborting the load.
    """
    saved_out = saved_err = devnull = None
    try:
        saved_out, saved_err = os.dup(1), os.dup(2)
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, 1)
        os.dup2(devnull, 2)
    except OSError:
        for fd in (devnull, saved_out, saved_err):
            if fd is not None:
                try:
                    os.close(fd)
                except OSError:
                    pass
        saved_out = saved_err = devnull = None

    try:
        yield
    finally:
        try:
            if saved_out is not None:
                os.dup2(saved_out, 1)
            if saved_err is not None:
                os.dup2(saved_err, 2)
        except OSError:
            pass
        for fd in (devnull, saved_out, saved_err):
            if fd is not None:
                try:
                    os.close(fd)
                except OSError:
                    pass


def load_model() -> SentenceTransformer:
    """
    Load the embedding model once (module-level singleton). Loading must never
    fail just because output-suppression doesn't work in this environment, so
    a failed suppressed load is retried plainly.

    Returns:
        SentenceTransformer: Loaded embedding model

    Raises:
        RuntimeError: If the model genuinely fails to load
    """
    global _model

    if _model is None:
        if MODEL_DIR.exists():
            source = str(MODEL_DIR)
            logger.info("Loading embedding model from local cache: %s", MODEL_DIR)
        else:
            source = MODEL_NAME
            logger.info("Downloading embedding model '%s' -> %s", MODEL_NAME, MODEL_DIR)

        try:
            with _suppress_native_output():
                _model = SentenceTransformer(source)
            if source == MODEL_NAME:
                MODEL_DIR.mkdir(parents=True, exist_ok=True)
                _model.save(str(MODEL_DIR))
                logger.info("Embedding model saved to %s", MODEL_DIR)
            logger.info("Embedding model ready")
        except Exception as e:
            logger.error("Failed to load embedding model: %s", e)
            raise RuntimeError(f"Embedding model load failed: {e}") from e

    return _model
