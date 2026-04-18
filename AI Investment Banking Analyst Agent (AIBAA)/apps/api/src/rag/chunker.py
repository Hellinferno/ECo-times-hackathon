"""Semantic text chunker for financial documents.

Splits parsed document text into overlapping windows that respect paragraph
boundaries. Each chunk stays within the LLM context budget while carrying
enough overlap to preserve cross-paragraph numerical continuity.

Design choices
--------------
- Paragraph-first split: financial reports use blank-line-separated sections
  (Income Statement, Balance Sheet, Notes) — keeping these intact improves
  retrieval precision.
- Target size ~800 chars with ~150-char overlap — balances granularity and
  context richness for Gemini's 1M token window.
- Each chunk carries its document_id, chunk index, and char offset so the
  retriever can surface citations back to the user.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List

_TARGET_CHUNK_CHARS = int(800)
_OVERLAP_CHARS = int(150)
_PARA_SPLIT = re.compile(r"\n{2,}")


@dataclass
class Chunk:
    document_id: str
    chunk_index: int
    text: str
    char_start: int
    char_end: int


def chunk_document(document_id: str, text: str) -> List[Chunk]:
    """Split *text* into overlapping chunks tied to *document_id*.

    Steps:
    1. Split on paragraph boundaries (two or more newlines).
    2. Greedily pack paragraphs into windows up to *_TARGET_CHUNK_CHARS*.
    3. When a window would exceed the target, seal it and start a new one
       that begins with the last *_OVERLAP_CHARS* of the previous window.

    Returns an ordered list of :class:`Chunk` objects.
    """
    if not text or not text.strip():
        return []

    paragraphs: List[str] = [p.strip() for p in _PARA_SPLIT.split(text) if p.strip()]

    chunks: List[Chunk] = []
    current_parts: List[str] = []
    current_len = 0
    current_start = 0  # char offset of first para in current window
    char_cursor = 0

    for para in paragraphs:
        para_len = len(para)

        if current_len + para_len > _TARGET_CHUNK_CHARS and current_parts:
            # Seal current chunk
            chunk_text = "\n\n".join(current_parts)
            chunks.append(
                Chunk(
                    document_id=document_id,
                    chunk_index=len(chunks),
                    text=chunk_text,
                    char_start=current_start,
                    char_end=current_start + len(chunk_text),
                )
            )

            # Overlap: carry the tail of the previous chunk text forward
            overlap_text = chunk_text[-_OVERLAP_CHARS:] if len(chunk_text) > _OVERLAP_CHARS else chunk_text
            current_parts = [overlap_text]
            current_len = len(overlap_text)
            current_start = char_cursor - _OVERLAP_CHARS if char_cursor > _OVERLAP_CHARS else 0

        current_parts.append(para)
        current_len += para_len
        char_cursor += para_len + 2  # +2 for "\n\n" separator

    # Flush the final window
    if current_parts:
        chunk_text = "\n\n".join(current_parts)
        chunks.append(
            Chunk(
                document_id=document_id,
                chunk_index=len(chunks),
                text=chunk_text,
                char_start=current_start,
                char_end=current_start + len(chunk_text),
            )
        )

    return chunks
