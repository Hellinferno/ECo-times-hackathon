from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timezone
from urllib.parse import urlparse

from database import SessionLocal
from db_models import DocumentModel
from persistence import sync_document_to_store
from rag.retriever import ingest_document
from store import store

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def update_document_rag_state(
    document_id: str,
    *,
    status: str,
    rag_error: str | None = None,
    rag_indexed_at: datetime | None = None,
) -> None:
    doc = store.documents.get(document_id)
    if doc:
        doc.rag_status = status
        doc.rag_error = rag_error
        doc.rag_indexed_at = rag_indexed_at
        store.documents[document_id] = doc

    with SessionLocal() as db:
        db_doc = db.query(DocumentModel).filter(DocumentModel.id == document_id).first()
        if not db_doc:
            return
        db_doc.rag_status = status
        db_doc.rag_error = rag_error
        db_doc.rag_indexed_at = rag_indexed_at
        db.commit()
        db.refresh(db_doc)
        sync_document_to_store(db_doc)


def perform_rag_indexing(document_id: str, deal_id: str, parsed_text: str | None = None) -> bool:
    doc = store.documents.get(document_id)
    text = parsed_text or getattr(doc, "parsed_text", None)

    if not text:
        update_document_rag_state(
            document_id,
            status="failed",
            rag_error="Parsed text unavailable for indexing.",
            rag_indexed_at=None,
        )
        return False

    update_document_rag_state(document_id, status="indexing", rag_error=None, rag_indexed_at=None)

    try:
        success = ingest_document(document_id, deal_id, text)
    except Exception as exc:
        logger.exception("RAG indexing failed for %s", document_id, exc_info=exc)
        update_document_rag_state(
            document_id,
            status="failed",
            rag_error=str(exc)[:240],
            rag_indexed_at=None,
        )
        return False

    if success:
        update_document_rag_state(
            document_id,
            status="indexed",
            rag_error=None,
            rag_indexed_at=_utcnow(),
        )
        return True

    update_document_rag_state(
        document_id,
        status="failed",
        rag_error="Vector store unavailable or ingest failed.",
        rag_indexed_at=None,
    )
    return False


async def _enqueue_rag_indexing(document_id: str, deal_id: str) -> bool:
    try:
        from arq import create_pool
        from arq.connections import RedisSettings
    except ImportError:
        return False

    parsed = urlparse(os.environ.get("REDIS_URL", "redis://localhost:6379/0"))
    redis_settings = RedisSettings(
        host=parsed.hostname or "localhost",
        port=parsed.port or 6379,
        database=int((parsed.path or "/0").lstrip("/")),
    )
    redis = await create_pool(redis_settings)
    try:
        job = await redis.enqueue_job("run_rag_indexing", document_id, deal_id)
        return job is not None
    finally:
        await redis.aclose()


def schedule_rag_indexing(document_id: str, deal_id: str) -> str:
    try:
        enqueued = asyncio.run(_enqueue_rag_indexing(document_id, deal_id))
    except Exception as exc:
        logger.debug("ARQ enqueue unavailable for %s: %s", document_id, exc)
        enqueued = False

    if enqueued:
        logger.info("Queued RAG indexing job for doc=%s", document_id)
        return "queued"

    success = perform_rag_indexing(document_id, deal_id)
    return "completed" if success else "failed"
