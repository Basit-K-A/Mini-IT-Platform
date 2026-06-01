"""
Centralized application settings from environment variables.

Keeps Redis, cache TTLs, and performance tuning in one place for Docker and local runs.
"""

import os
from functools import lru_cache


def _bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


@lru_cache
def get_settings() -> "Settings":
    return Settings()


class Settings:
    """Read once per process; use get_settings() in application code."""

    def __init__(self) -> None:
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.redis_enabled = _bool(os.getenv("REDIS_ENABLED"), default=True)
        self.redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
        self.redis_socket_timeout = float(os.getenv("REDIS_SOCKET_TIMEOUT", "2.0"))

        # Cache TTLs (seconds)
        self.cache_ttl_dashboard = int(os.getenv("CACHE_TTL_DASHBOARD", "120"))
        self.cache_ttl_stats = int(os.getenv("CACHE_TTL_STATS", "300"))
        self.cache_ttl_list = int(os.getenv("CACHE_TTL_LIST", "60"))

        # Performance
        self.slow_query_ms = int(os.getenv("SLOW_QUERY_MS", "500"))
        self.slow_request_ms = int(os.getenv("SLOW_REQUEST_MS", "1000"))

        # DB pool (horizontal scaling prep)
        self.db_pool_size = int(os.getenv("DB_POOL_SIZE", "5"))
        self.db_max_overflow = int(os.getenv("DB_MAX_OVERFLOW", "10"))
