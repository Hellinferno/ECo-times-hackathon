"""ARQ background worker entry point.

Run with: python -m src.worker  (from apps/api/)
Falls back gracefully if Redis is unavailable.
"""
import logging
import os
import sys
from pathlib import Path

# Ensure src is on sys.path (same trick as main.py)
src_path = Path(__file__).parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from logging_config import configure_logging

configure_logging()
logger = logging.getLogger(__name__)

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")


async def startup(ctx: dict) -> None:
    from database import SessionLocal

    ctx["db"] = SessionLocal()
    logger.info("Worker started")


async def shutdown(ctx: dict) -> None:
    db = ctx.get("db")
    if db:
        db.close()
    logger.info("Worker stopped")


async def run_rag_indexing(ctx: dict, document_id: str, deal_id: str) -> None:
    """ARQ task: ingest a parsed document into the vector store."""
    from rag.indexing import perform_rag_indexing

    success = perform_rag_indexing(document_id, deal_id)
    logger.info("run_rag_indexing: doc=%s status=%s", document_id, "indexed" if success else "failed")


class WorkerSettings:
    """ARQ worker settings — discovered by arq CLI."""

    redis_settings = None  # Set dynamically below
    on_startup = startup
    on_shutdown = shutdown
    functions: list = [run_rag_indexing]
    max_jobs = 4


def _configure_redis_settings() -> None:
    try:
        from arq.connections import RedisSettings
        from urllib.parse import urlparse

        parsed = urlparse(REDIS_URL)
        WorkerSettings.redis_settings = RedisSettings(
            host=parsed.hostname or "localhost",
            port=parsed.port or 6379,
            database=int((parsed.path or "/0").lstrip("/")),
        )
    except ImportError:
        logger.warning("arq not installed — worker cannot start")


_configure_redis_settings()
