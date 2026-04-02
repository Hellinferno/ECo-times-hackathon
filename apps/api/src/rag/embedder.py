"""Sentence-transformers embedding generator.

Uses `all-MiniLM-L6-v2` (384-dim, ~22 MB) — fast enough to run on CPU during
document ingestion without blocking the API event loop, and accurate enough
for financial terminology retrieval.

The model is loaded lazily on first use and cached for the process lifetime.
Encoding is batched to amortise tokenisation overhead over many chunks.
"""

from __future__ import annotations

import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

_MODEL_NAME = "all-MiniLM-L6-v2"
_encoder = None  # lazy singleton


def _get_encoder():
    global _encoder
    if _encoder is not None:
        return _encoder
    try:
        from sentence_transformers import SentenceTransformer
        _encoder = SentenceTransformer(_MODEL_NAME)
        logger.info("[RAG/embedder] Loaded %s", _MODEL_NAME)
    except Exception as exc:
        logger.error("[RAG/embedder] Could not load sentence-transformers: %s", exc)
        _encoder = None
    return _encoder


def embed_texts(texts: List[str]) -> Optional[List[List[float]]]:
    """Return a list of embedding vectors for *texts*, or None on failure.

    Each embedding is a list of 384 floats. ChromaDB accepts Python lists
    directly so no numpy conversion is needed.
    """
    if not texts:
        return []

    encoder = _get_encoder()
    if encoder is None:
        return None

    try:
        vectors = encoder.encode(texts, batch_size=32, show_progress_bar=False)
        return [v.tolist() for v in vectors]
    except Exception as exc:
        logger.error("[RAG/embedder] encode() failed: %s", exc)
        return None


def embed_query(query: str) -> Optional[List[float]]:
    """Embed a single query string for retrieval. Returns None on failure."""
    result = embed_texts([query])
    if result:
        return result[0]
    return None
