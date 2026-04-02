"""ChromaDB persistent vector store wrapper.

One ChromaDB collection holds ALL document chunks across all deals.
Each chunk is stored with metadata so queries can be scoped per document
or per deal without separate collections.

Collection schema
-----------------
  id        : "{document_id}_{chunk_index}"
  document  : chunk text
  embedding : 384-dim float list (all-MiniLM-L6-v2)
  metadata  : {
      "document_id" : str,
      "deal_id"     : str,
      "chunk_index" : int,
      "char_start"  : int,
      "char_end"    : int,
  }

Storage
-------
Uses `chromadb.PersistentClient` with the directory from `AIBAA_CHROMA_DIR`
(default: `./chroma_data` relative to the running process). In Docker, this
is mounted as the `chromadata` volume.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_COLLECTION_NAME = "aibaa_documents"
_CHROMA_DIR = os.environ.get("AIBAA_CHROMA_DIR", str(Path(__file__).resolve().parents[3] / "chroma_data"))

_chroma_client = None
_collection = None


def get_chroma_store():
    """Return the ChromaDB collection, initialising the client if needed.

    Returns None if ChromaDB is unavailable (graceful degradation — the rest
    of the pipeline falls back to raw parsed_text context).
    """
    global _chroma_client, _collection

    if _collection is not None:
        return _collection

    try:
        import chromadb

        Path(_CHROMA_DIR).mkdir(parents=True, exist_ok=True)
        _chroma_client = chromadb.PersistentClient(path=_CHROMA_DIR)
        _collection = _chroma_client.get_or_create_collection(
            name=_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info("[RAG/store] ChromaDB ready at %s (collection=%s)", _CHROMA_DIR, _COLLECTION_NAME)
        return _collection
    except Exception as exc:
        logger.warning("[RAG/store] ChromaDB unavailable: %s", exc)
        return None


def delete_document_chunks(document_id: str) -> None:
    """Remove all chunks belonging to *document_id* from the store."""
    collection = get_chroma_store()
    if collection is None:
        return
    try:
        collection.delete(where={"document_id": document_id})
        logger.debug("[RAG/store] Deleted chunks for doc=%s", document_id)
    except Exception as exc:
        logger.warning("[RAG/store] delete_document_chunks failed: %s", exc)
