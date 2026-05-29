"""
Application entry point.

main.py should stay small:
- create the FastAPI app
- register routers
- run startup tasks (e.g. create tables)
"""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import OperationalError
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

import models  # noqa: F401 — registers ORM models with Base.metadata
from database import Base, check_database_connection, engine
from logging_config import setup_logging
from middleware.request_logging import RequestLoggingMiddleware
from routers import audit, auth, devices, events, health

setup_logging()
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
    title="Nexventory API",
    description="Internal IT platform API with JWT auth and PostgreSQL",
    lifespan=lifespan,
)

# Honor X-Forwarded-* from nginx (scheme, host, client IP for logs/rate limits later)
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")
app.add_middleware(RequestLoggingMiddleware)

# Comma-separated origins for the React dashboard (e.g. http://localhost:5173)
_cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _cors_origins.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(audit.router)
app.include_router(devices.router)
app.include_router(events.router)
