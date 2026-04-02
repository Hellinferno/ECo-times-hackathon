"""RAG retriever — ingest documents and retrieve relevant context.

Two public entry points:

ingest_document(document_id, deal_id, parsed_text)
    Called after a document is parsed. Chunks the text, embeds each chunk,
    and upserts all chunks into the ChromaDB collection.

retrieve_context(query, document_id, top_k)
    Given a natural-language query and a document scope, returns the top-k
    most relevant text chunks concatenated as a single string ready for
    injection into an agent system prompt.

Both functions degrade gracefully if ChromaDB or the sentence-transformers
model are unavailable — callers receive None / empty string and fall back
to the existing raw-text path.
"""

from __future__ import annotations

import logging
from typing import Optional

from rag.chunker import chunk_document
from rag.embedder import embed_texts, embed_query
from rag.store import get_chroma_store, delete_document_chunks

logger = logging.getLogger(__name__)

_DEFAULT_TOP_K = 8


def ingest_document(document_id: str, deal_id: str, parsed_text: str) -> bool:
    """Chunk, embed, and store *parsed_text* in ChromaDB.

    Returns True on success, False if ChromaDB or the embedder is unavailable.
    Idempotent: existing chunks for the document are deleted first.
    """
    collection = get_chroma_store()
    if collection is None:
        return False

    chunks = chunk_document(document_id, parsed_text)
    if not chunks:
        logger.debug("[RAG/retriever] ingest: no chunks for doc=%s", document_id)
        return False

    texts = [c.text for c in chunks]
    vectors = embed_texts(texts)
    if vectors is None:
        logger.warning("[RAG/retriever] ingest: embedding failed for doc=%s", document_id)
        return False

    # Remove stale chunks before upserting (re-parse scenario)
    delete_document_chunks(document_id)

    ids = [f"{document_id}_{c.chunk_index}" for c in chunks]
    metadatas = [
        {
            "document_id": document_id,
            "deal_id": deal_id,
            "chunk_index": c.chunk_index,
            "char_start": c.char_start,
            "char_end": c.char_end,
        }
        for c in chunks
    ]

    try:
        collection.upsert(
            ids=ids,
            documents=texts,
            embeddings=vectors,
            metadatas=metadatas,
        )
        logger.info(
            "[RAG/retriever] Ingested %d chunks for doc=%s (deal=%s)",
            len(chunks), document_id, deal_id,
        )
        return True
    except Exception as exc:
        logger.error("[RAG/retriever] upsert failed: %s", exc)
        return False


def retrieve_chunk_records(
    query: str,
    *,
    document_id: str | None = None,
    deal_id: str | None = None,
    top_k: int = _DEFAULT_TOP_K,
) -> Optional[list[dict]]:
    """Return ranked chunk records for a document or deal scope."""
    collection = get_chroma_store()
    if collection is None:
        return None

    query_vec = embed_query(query)
    if query_vec is None:
        return None

    scope_filter = {"document_id": document_id} if document_id else {"deal_id": deal_id}
    if not scope_filter.get("document_id") and not scope_filter.get("deal_id"):
        return None

    count = collection.count()
    if count <= 0:
        return None

    try:
        results = collection.query(
            query_embeddings=[query_vec],
            n_results=min(top_k, count),
            where=scope_filter,
            include=["documents", "distances", "metadatas"],
        )
    except Exception as exc:
        logger.warning("[RAG/retriever] query failed: %s", exc)
        return None

    docs = results.get("documents", [[]])[0]
    distances = results.get("distances", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    if not docs:
        return None

    return [
        {
            "rank": idx + 1,
            "text": doc,
            "distance": distances[idx] if idx < len(distances) else None,
            "metadata": metadatas[idx] if idx < len(metadatas) else {},
        }
        for idx, doc in enumerate(docs)
    ]


def retrieve_context(
    query: str,
    document_id: str,
    top_k: int = _DEFAULT_TOP_K,
) -> Optional[str]:
    """Return the top-*k* relevant chunks for *query* scoped to *document_id*.

    Returns a single string (chunks joined by a separator) suitable for
    injection into an agent prompt, or None if retrieval is unavailable.

    The caller should fall back to the full parsed_text when this returns None.
    """
    chunks = retrieve_chunk_records(query, document_id=document_id, top_k=top_k)
    if not chunks:
        return None

    separator = "\n\n---\n\n"
    return separator.join(chunk["text"] for chunk in chunks)
