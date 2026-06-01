"""
Redis connection management — optional cache layer with graceful degradation.

If Redis is disabled or unreachable, the API continues against PostgreSQL only.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from core.settings import get_settings

if TYPE_CHECKING:
    import redis

logger = logging.getLogger(__name__)

_client: redis.Redis | None = None
_available: bool = False


def init_redis() -> None:
    """Connect at startup; failures are logged and the app runs without cache."""
    global _client, _available
    settings = get_settings()
    if not settings.redis_enabled:
        logger.info("Redis caching disabled (REDIS_ENABLED=false)")
        _available = False
        return

    try:
        import redis as redis_lib

        _client = redis_lib.Redis.from_url(
            settings.redis_url,
            decode_responses=True,
            socket_connect_timeout=settings.redis_socket_timeout,
            socket_timeout=settings.redis_socket_timeout,
        )
        _client.ping()
        _available = True
        logger.info("Redis connected at %s", settings.redis_url.split("@")[-1])
    except Exception as exc:
        _client = None
        _available = False
        logger.warning("Redis unavailable — caching disabled: %s", exc)


def close_redis() -> None:
    global _client, _available
    if _client is not None:
        try:
            _client.close()
        except Exception:
            pass
    _client = None
    _available = False


def is_redis_available() -> bool:
    return _available and _client is not None


def get_redis() -> redis.Redis | None:
    return _client if is_redis_available() else None
