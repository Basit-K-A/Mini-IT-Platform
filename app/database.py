"""
Database connection setup.

Responsible for:
- Loading DATABASE_URL from .env
- Creating the SQLAlchemy engine and SessionLocal factory
- Providing the get_db() dependency for FastAPI routes
- Slow-query logging for performance monitoring
"""

import logging
import os
import time
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import declarative_base, sessionmaker

from core.settings import get_settings

logger = logging.getLogger(__name__)
perf_logger = logging.getLogger("nexventory.performance")


def load_dotenv_files() -> None:
    """
    Load environment variables from .env files.

    Order: project root first, then app/ (app values override root).
    Docker Compose injects DATABASE_URL with host "db"; local runs use localhost.
    """
    root_env = Path(__file__).resolve().parent.parent / ".env"
    app_env = Path(__file__).resolve().parent / ".env"
    loaded = False
    for path in (root_env, app_env):
        if path.is_file():
            load_dotenv(path)
            loaded = True
    if not loaded:
        load_dotenv()


load_dotenv_files()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:password@localhost:5432/mini_it_platform",
)


def log_database_target() -> None:
    """Log connection target without secrets (no password)."""
    parsed = urlparse(DATABASE_URL)
    logger.info(
        "Database config: host=%s port=%s database=%s user=%s",
        parsed.hostname or "(missing)",
        parsed.port or 5432,
        (parsed.path or "").lstrip("/") or "(missing)",
        parsed.username or "(missing)",
    )


log_database_target()

_settings = get_settings()
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=_settings.db_pool_size,
    max_overflow=_settings.db_max_overflow,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def _register_slow_query_logging() -> None:
    """Log SQL statements that exceed SLOW_QUERY_MS (ORM + Core)."""
    threshold_ms = get_settings().slow_query_ms

    @event.listens_for(engine, "before_cursor_execute")
    def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        conn.info.setdefault("query_start_time", []).append(time.perf_counter())

    @event.listens_for(engine, "after_cursor_execute")
    def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        started = conn.info.get("query_start_time", []).pop() if conn.info.get("query_start_time") else None
        if started is None:
            return
        duration_ms = (time.perf_counter() - started) * 1000
        if duration_ms >= threshold_ms:
            perf_logger.warning(
                "Slow query detected: duration_ms=%.2f statement=%s",
                duration_ms,
                (statement or "")[:500],
            )


_register_slow_query_logging()


def check_database_connection() -> None:
    """Verify DB connectivity at startup. Raises sqlalchemy.exc.OperationalError on failure."""
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))


def get_db():
    """
    FastAPI dependency: opens a DB session for one request, then closes it.

    Usage in a route:
        def my_route(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
