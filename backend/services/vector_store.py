# services/vector_store.py
"""
ChromaDB vector store for cross-source semantic deduplication.

The same job often appears on both Adzuna and Arbeitnow with different ids,
so id-dedup misses it. We embed each scored job's title+company and, before
scoring a new job, check the store for a near-duplicate - avoiding a wasted
extraction/score (and LLM tokens) on the same role twice.

Embeddings come from the same local sentence-transformers model used for
matching (no tokens). Fails soft: if Chroma is unavailable, dedup is simply
skipped and the rest of the pipeline runs normally.
"""

from pathlib import Path

from matcher.embedding_model import load_model
from core.logger import get_logger

logger = get_logger(__name__)

CHROMA_PATH = Path("data/chroma")
_SIM_THRESHOLD = 0.93  # cosine similarity above which two jobs are "the same"

_col = None
_client = None


def _collection():
    """Lazily open (or create) the persistent 'jobs' collection."""
    global _client, _col
    if _col is not None:
        return _col
    try:
        import chromadb

        CHROMA_PATH.mkdir(parents=True, exist_ok=True)
        _client = chromadb.PersistentClient(path=str(CHROMA_PATH))
        _col = _client.get_or_create_collection(
            "jobs", metadata={"hnsw:space": "cosine"}
        )
    except Exception as e:
        logger.error("ChromaDB unavailable - dedup disabled: %s", e)
        _col = None
    return _col


def _embed(job) -> list:
    return load_model().encode(f"{job.title} {job.company}".strip()).tolist()


def is_duplicate(job) -> bool:
    """True if a near-identical job (different id) is already stored."""
    col = _collection()
    if col is None or not job.id:
        return False
    try:
        if col.count() == 0:
            return False
        res = col.query(query_embeddings=[_embed(job)], n_results=1)
        ids = (res.get("ids") or [[]])[0]
        dists = (res.get("distances") or [[]])[0]
        if ids and dists and ids[0] != job.id:
            sim = 1.0 - dists[0]
            if sim >= _SIM_THRESHOLD:
                logger.info(
                    "Duplicate: '%s' ~ stored '%s' (sim %.2f)",
                    job.title[:30],
                    ids[0],
                    sim,
                )
                return True
    except Exception as e:
        logger.error("dedup query failed: %s", e)
    return False


def add(job) -> None:
    """Register a job so future near-duplicates are detected."""
    col = _collection()
    if col is None or not job.id:
        return
    try:
        col.upsert(
            ids=[job.id],
            embeddings=[_embed(job)],
            metadatas=[
                {"title": job.title, "company": job.company, "source": job.source}
            ],
        )
    except Exception as e:
        logger.error("vector add failed: %s", e)


def clear() -> None:
    """Drop all stored job vectors."""
    global _col
    col = _collection()
    if col is None:
        return
    try:
        _client.delete_collection("jobs")
        _col = None
    except Exception as e:
        logger.error("vector clear failed: %s", e)
