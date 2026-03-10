# src/matcher/model.py

from sentence_transformers import SentenceTransformer

# LOAD MODEL ONCE
# Module level singleton — loads only on first import
# No Streamlit cache needed — plain Python works fine

_model = None


def load_model():
    """
    Load sentence-transformers model once.
    Cached at module level — never reloads.

    Returns:
        SentenceTransformer: Loaded model
    """
    global _model
    if _model is None:
        print("Loading sentence-transformers model...")
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model