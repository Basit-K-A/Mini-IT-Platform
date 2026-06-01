"""
Shared pytest fixtures.

Tests run against a **separate, in-memory SQLite database** so they never touch
the real PostgreSQL instance. We:

- set safe env vars before importing any app module,
- build an isolated SQLAlchemy engine + session factory,
- override the FastAPI ``get_db`` dependency to use it,
- disable rate limiting and route background-task DB writes to the test DB,
- reset all tables between tests for isolation.

None of this changes production behavior — it only wires the app to a throwaway
database for the duration of the test run.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from types import SimpleNamespace

# --- Environment must be configured BEFORE importing app modules -------------
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production-0123456789abcdef")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "15")

# Flat app layout: make `auth`, `crud`, `models`, ... importable.
APP_DIR = Path(__file__).resolve().parent.parent / "app"
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

import models  # noqa: E402,F401  (registers ORM models on Base.metadata)
from database import Base, get_db  # noqa: E402

# Isolated test database. StaticPool keeps a single shared in-memory connection
# so every session in a test sees the same data.
test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=test_engine, autoflush=False, autocommit=False)


@pytest.fixture(autouse=True)
def _reset_database():
    """Fresh schema for every test."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session():
    """Direct DB session for unit/CRUD tests."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client():
    """TestClient with get_db overridden, rate limiting off, background DB redirected."""
    from core.limiter import limiter
    from main import app
    import services.background_tasks as background_tasks

    def _override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = _override_get_db
    limiter.enabled = False
    original_session_local = background_tasks.SessionLocal
    background_tasks.SessionLocal = TestingSessionLocal

    # NOTE: no `with` — we intentionally skip the app lifespan so tests never try
    # to reach the real PostgreSQL/Redis. Tables live on the SQLite test engine.
    test_client = TestClient(app)
    try:
        yield test_client
    finally:
        app.dependency_overrides.clear()
        background_tasks.SessionLocal = original_session_local


@pytest.fixture
def make_user(db_session):
    """Factory to persist a user with a hashed password and given role."""
    from auth.security import get_password_hash
    from models.user import User

    def _make(
        username: str = "tester",
        role: str = "viewer",
        password: str = "StrongP@ss1",
        is_active: bool = True,
        email: str | None = None,
    ) -> User:
        user = User(
            username=username,
            email=email or f"{username}@example.com",
            hashed_password=get_password_hash(password),
            role=role,
            is_active=is_active,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user

    return _make


@pytest.fixture
def auth_header():
    """Build an Authorization header with a valid access token for a username."""
    from auth.jwt_handler import create_access_token

    def _header(username: str) -> dict[str, str]:
        token = create_access_token({"sub": username})
        return {"Authorization": f"Bearer {token}"}

    return _header


@pytest.fixture
def fake_request():
    """Minimal stand-in for a Starlette Request usable by audit/IP helpers."""

    def _make(path: str = "/test"):
        return SimpleNamespace(
            url=SimpleNamespace(path=path),
            headers={},  # dict.get(...) → None, mimicking missing headers
            client=None,
        )

    return _make
