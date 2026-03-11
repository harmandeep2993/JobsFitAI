# src/matcher/embedding_model.py

"""
Sentence-transformers embedding model loader.
Loads the model once and reuses it across the application.
"""

from sentence_transformers import SentenceTransformer


MODEL_NAME = "all-MiniLM-L6-v2"

_model = None


def load_model():
    """
    Load embedding model once (module-level singleton).

    Returns:
        SentenceTransformer
    """
    global _model

    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)

    return _model