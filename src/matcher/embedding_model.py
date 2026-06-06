# src/matcher/embedding_model.py

"""
Sentence-transformers embedding model loader.
Loads the model once and reuses it across the application.
"""

from sentence_transformers import SentenceTransformer
from src.utils import get_logger

logger = get_logger(__name__)

# Multilingual model — supports 50+ languages including all European languages
# Swap to paraphrase-multilingual-mpnet-base-v2 for better quality at cost of speed
# MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

_model = None


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
            _model = SentenceTransformer(MODEL_NAME)
            logger.info("Embedding model loaded successfully")
        except Exception as e:
            logger.error("Failed to load embedding model: %s", e)
            raise RuntimeError(f"Embedding model load failed: {e}") from e

    return _model