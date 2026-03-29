"""SQLAlchemy engine and session factory.

Exposes:
- ``engine``        — shared engine instance (SQLite for local dev, PostgreSQL in prod)
- ``SessionLocal``  — session factory used throughout the app
- ``get_db``        — FastAPI dependency that yields a request-scoped DB session
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import settings

database_url = settings.database_url
_is_sqlite = database_url.startswith("sqlite")

engine = create_engine(
    database_url,
    connect_args={"check_same_thread": False} if _is_sqlite else {},
    # pool_pre_ping keeps connections healthy in long-running cloud deployments
    pool_pre_ping=not _is_sqlite,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """FastAPI dependency: yields a DB session and guarantees it is closed."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
