# src/matcher/embedding_model.py

"""
Sentence-transformers embedding model loader.
Loads the model once and reuses it across the application.
"""

import os
import contextlib

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

# Multilingual model — supports 50+ languages including all European languages
# Swap to paraphrase-multilingual-mpnet-base-v2 for better quality at cost of speed
# MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

_model = None


@contextlib.contextmanager
def _suppress_native_output():
    """Redirect fd 1 & 2 to devnull so native/library prints are silenced."""
    saved_out, saved_err = os.dup(1), os.dup(2)
    devnull = os.open(os.devnull, os.O_WRONLY)
    try:
        os.dup2(devnull, 1)
        os.dup2(devnull, 2)
        yield
    finally:
        os.dup2(saved_out, 1)
        os.dup2(saved_err, 2)
        os.close(devnull)
        os.close(saved_out)
        os.close(saved_err)


def load_model() -> SentenceTransformer:
    """
    Load embedding model once (module-level singleton).
    Model is downloaded on first call and cached locally by sentence-transformers.

    Returns:
        SentenceTransformer: Loaded embedding model

    Raises:
        RuntimeError: If model fails to load
    """
    global _model

    if _model is None:
        logger.info("Loading embedding model: %s", MODEL_NAME)
        try:
            # Silence the weights progress bar / "LOAD REPORT" the transformers
            # loader writes straight to the stdout/stderr file descriptors
            # (bypasses Python-level redirect), by redirecting fds 1 & 2.
            with _suppress_native_output():
                _model = SentenceTransformer(MODEL_NAME)
            logger.info("Embedding model loaded successfully")
        except Exception as e:
            logger.error("Failed to load embedding model: %s", e)
            raise RuntimeError(f"Embedding model load failed: {e}") from e

    return _model