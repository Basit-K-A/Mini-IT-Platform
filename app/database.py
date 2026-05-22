"""
Database connection setup.

Responsible for:
- Loading DATABASE_URL from .env
- Creating the SQLAlchemy engine and SessionLocal factory
- Providing the get_db() dependency for FastAPI routes
"""

import logging
import os
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

logger = logging.getLogger(__name__)


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

# Default for local dev on the host (Docker Compose overrides via environment).
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

# pool_pre_ping: avoids stale connections after db container restarts
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# Each request gets its own database session via SessionLocal()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all ORM models (User, Device, Ticket, etc.)
Base = declarative_base()


def check_database_connection() -> None:
    """Verify DB connectivity at startup. Raises sqlalchemy.exc.OperationalError on failure."""
    from sqlalchemy import text

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
