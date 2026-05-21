"""
Database connection setup.

Responsible for:
- Loading DATABASE_URL from .env
- Creating the SQLAlchemy engine and SessionLocal factory
- Providing the get_db() dependency for FastAPI routes
"""

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Load variables from a .env file in the project root (app/)
load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/mini_it_platform",
)

# sync engine (no async SQLAlchemy in this project yet)
engine = create_engine(DATABASE_URL)

# Each request gets its own database session via SessionLocal()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all ORM models (User, Device, Ticket, etc.)
Base = declarative_base()


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
