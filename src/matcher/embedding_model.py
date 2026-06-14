# src/matcher/embedding_model.py

"""
Sentence-transformers embedding model loader.
Loads the model once and reuses it across the application.
"""

import contextlib
import os

# Quiet HuggingFace/transformers noise before they're imported below
# (progress bars, advisory warnings, the model "LOAD REPORT").
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")
os.environ.setdefault("TRANSFORMERS_NO_ADVISORY_WARNINGS", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

from sentence_transformers import SentenceTransformer

try:
    from transformers.utils import logging as _hf_logging

    _hf_logging.set_verbosity_error()
except Exception:
    pass

from src.utils import get_logger

logger = get_logger(__name__)

# Multilingual model - supports 50+ languages including all European languages
# Swap to paraphrase-multilingual-mpnet-base-v2 for better quality at cost of speed
# MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

_model = None


@contextlib.contextmanager
def _suppress_native_output():
    """
    Best-effort: redirect fd 1 & 2 to devnull to silence native/library prints
    (the weights bar / "LOAD REPORT"). If the fds can't be duplicated - e.g.
    inside a server threadpool on Windows, which raised WinError 1 - this
    yields WITHOUT redirecting so the caller still runs normally.
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
        logger.info("Loading embedding model: %s", MODEL_NAME)
        try:
            try:
                with _suppress_native_output():
                    _model = SentenceTransformer(MODEL_NAME)
            except Exception:
                # Suppression context interfered (e.g. WinError 1) - load plainly.
                _model = SentenceTransformer(MODEL_NAME)
            logger.info("Embedding model loaded successfully")
        except Exception as e:
            logger.error("Failed to load embedding model: %s", e)
            raise RuntimeError(f"Embedding model load failed: {e}") from e

    return _model
