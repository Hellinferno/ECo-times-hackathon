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


class WorkerSettings:
    """ARQ worker settings — discovered by arq CLI."""

    redis_settings = None  # Set dynamically below
    on_startup = startup
    on_shutdown = shutdown
    functions: list = []  # Register task functions here as needed
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
