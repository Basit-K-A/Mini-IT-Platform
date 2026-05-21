"""
Application entry point.

main.py should stay small:
- create the FastAPI app
- register routers
- run startup tasks (e.g. create tables)
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

import models  # noqa: F401 — registers ORM models with Base.metadata
from database import Base, engine
from routers import auth


@asynccontextmanager
async def lifespan(app: FastAPI):
    # For a portfolio project, create_all() is enough to bootstrap tables.
    # Later you can replace this with Alembic migrations.
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Mini IT Platform",
    description="Internal IT platform API with JWT auth and PostgreSQL",
    lifespan=lifespan,
)

app.include_router(auth.router)
