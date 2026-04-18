"""RAG (Retrieval-Augmented Generation) pipeline for AIBAA.

Phase 2 components:
  chunker   — split parsed document text into overlapping chunks
  embedder  — generate sentence-transformers embeddings
  store     — ChromaDB persistent vector store wrapper
  retriever — query-time top-k retrieval for agent context injection
"""
from rag.chunker import chunk_document
from rag.store import get_chroma_store
from rag.retriever import retrieve_context, ingest_document

__all__ = ["chunk_document", "get_chroma_store", "retrieve_context", "ingest_document"]
