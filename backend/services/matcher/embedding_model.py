# services/matcher/embedding_model.py

"""
Sentence-transformers embedding model loader.
Loads the model once and reuses it across the application.
"""

import os
from pathlib import Path

# Silence HuggingFace/transformers/tqdm noise before imports.
# TQDM_DISABLE is checked per-instance at tqdm.__init__ time, so setting it
# here suppresses all progress bars for the entire process lifetime.
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")
os.environ.setdefault("TRANSFORMERS_NO_ADVISORY_WARNINGS", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ["TQDM_DISABLE"] = "1"

from sentence_transformers import SentenceTransformer

try:
    from transformers.utils import logging as _hf_logging

    _hf_logging.set_verbosity_error()
except Exception:
    pass

from core.logger import get_logger

logger = get_logger(__name__)

# Multilingual model - supports 50+ languages including all European languages
MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
MODEL_SHORT = MODEL_NAME.split("/")[-1]

# Local cache inside the project - loaded directly without any HF Hub lookup.
# Falls back to downloading from HuggingFace on first run, then saves here.
MODEL_DIR = Path(__file__).parent.parent.parent / "data" / "models" / MODEL_SHORT

_model = None


def load_model() -> SentenceTransformer:
    """
    Load the embedding model once (module-level singleton).

    On first call: loads from data/models/ if present, otherwise downloads
    from HuggingFace and saves locally for future runs.

    Returns:
        SentenceTransformer: Loaded embedding model

    Raises:
        RuntimeError: If the model fails to load
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
