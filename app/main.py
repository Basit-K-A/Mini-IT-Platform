"""
Application entry point.

main.py should stay small:
- create the FastAPI app
- register routers
- run startup tasks (e.g. create tables)
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.exc import OperationalError

import models  # noqa: F401 — registers ORM models with Base.metadata
from database import Base, check_database_connection, engine
from routers import auth

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # For a portfolio project, create_all() is enough to bootstrap tables.
    # Later you can replace this with Alembic migrations.
    try:
        check_database_connection()
        Base.metadata.create_all(bind=engine)
        logger.info("Database connected and tables are ready.")
    except OperationalError as exc:
        from urllib.parse import urlparse

        from database import DATABASE_URL

        parsed = urlparse(DATABASE_URL)
        logger.error(
            "Database unavailable at startup — API will run but DB routes will fail. "
            "host=%s port=%s database=%s user=%s. Error: %s",
            parsed.hostname,
            parsed.port or 5432,
            (parsed.path or "").lstrip("/"),
            parsed.username,
            exc,
        )
    yield


app = FastAPI(
    title="Mini IT Platform",
    description="Internal IT platform API with JWT auth and PostgreSQL",
    lifespan=lifespan,
)

app.include_router(auth.router)
