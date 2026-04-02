import os
from threading import Lock

from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

load_dotenv()

# We default to SQLite for immediate local dev compatibility without forcing the user to spin up Docker Postgres immediately,
# but the code is fully Postgres-ready based on the DB_URL format.
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./aibaa.db")

# SQLite requires this connect_args flag. Postgres does not.
connect_args = {"check_same_thread": False} if SQLALCHEMY_DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args=connect_args
)
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    bind=engine,
)

Base = declarative_base()
_schema_ready = False
_schema_lock = Lock()


def _ensure_nullable_column(table_name: str, column_name: str, ddl: str) -> None:
    inspector = inspect(engine)
    if table_name not in inspector.get_table_names():
        return

    existing = {col["name"] for col in inspector.get_columns(table_name)}
    if column_name in existing:
        return

    with engine.begin() as conn:
        conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {ddl}"))


def _ensure_schema_compatibility() -> None:
    """Apply lightweight additive schema fixes for local/dev databases."""
    _ensure_nullable_column("documents", "rag_indexed_at", "DATETIME")
    _ensure_nullable_column("documents", "rag_error", "VARCHAR")


def ensure_database_ready() -> None:
    """Create tables lazily for direct module/test usage outside FastAPI startup."""
    global _schema_ready
    if _schema_ready:
        return

    with _schema_lock:
        if _schema_ready:
            return
        import db_models  # noqa: F401 - ensure metadata is registered before create_all

        Base.metadata.create_all(bind=engine)
        _ensure_schema_compatibility()
        _schema_ready = True

def get_db():
    ensure_database_ready()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
