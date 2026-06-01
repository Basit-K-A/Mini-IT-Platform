"""
API response cache — Redis-backed with hit/miss logging and PostgreSQL fallback.

Cache keys are namespaced (dashboard:, stats:, list:) for targeted invalidation.
"""

from __future__ import annotations

import hashlib
import json
import logging
from collections.abc import Callable
from typing import Any, TypeVar

from pydantic import BaseModel

from core.redis_client import get_redis, is_redis_available
from core.settings import get_settings
from services.cache_keys import CacheKeys

logger = logging.getLogger("nexventory.cache")

T = TypeVar("T")


def _serialize(value: Any) -> str:
    if isinstance(value, BaseModel):
        return value.model_dump_json()
    return json.dumps(value, default=str)


def _deserialize(raw: str, model: type[BaseModel] | None = None) -> Any:
    if model is not None:
        return model.model_validate_json(raw)
    return json.loads(raw)


def make_list_cache_key(resource: str, params: Any) -> str:
    """Stable key from list query params (pagination + filters)."""
    if hasattr(params, "model_dump"):
        payload = params.model_dump()
    elif hasattr(params, "__dict__"):
        payload = {k: v for k, v in vars(params).items() if not k.startswith("_")}
    else:
        payload = dict(params)
    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True, default=str).encode()
    ).hexdigest()[:16]
    return CacheKeys.list(resource, digest)


def cache_get(key: str, model: type[BaseModel] | None = None) -> Any | None:
    client = get_redis()
    if not client:
        return None
    try:
        raw = client.get(key)
        if raw is None:
            logger.info("CACHE MISS: %s", key)
            return None
        logger.info("CACHE HIT: %s", key)
        return _deserialize(raw, model)
    except Exception as exc:
        logger.warning("CACHE ERROR on get %s: %s", key, exc)
        return None


def cache_set(key: str, value: Any, ttl_seconds: int) -> None:
    client = get_redis()
    if not client:
        return
    try:
        client.setex(key, ttl_seconds, _serialize(value))
    except Exception as exc:
        logger.warning("CACHE ERROR on set %s: %s", key, exc)


def cache_delete(key: str) -> None:
    client = get_redis()
    if not client:
        return
    try:
        client.delete(key)
        logger.debug("CACHE DELETE: %s", key)
    except Exception as exc:
        logger.warning("CACHE ERROR on delete %s: %s", key, exc)


def cache_delete_pattern(pattern: str) -> int:
    """Delete keys matching pattern (use sparingly; fine for modest key counts)."""
    client = get_redis()
    if not client:
        return 0
    deleted = 0
    try:
        for key in client.scan_iter(match=pattern, count=100):
            client.delete(key)
            deleted += 1
        if deleted:
            logger.info("CACHE INVALIDATE pattern=%s count=%d", pattern, deleted)
    except Exception as exc:
        logger.warning("CACHE ERROR on pattern %s: %s", pattern, exc)
    return deleted


def get_or_set(
    key: str,
    ttl_seconds: int,
    builder: Callable[[], T],
    *,
    model: type[BaseModel] | None = None,
) -> T:
    """
    Return cached value or compute, store, and return.

    Always calls builder when Redis is unavailable (graceful fallback).
    """
    if is_redis_available():
        cached = cache_get(key, model=model)
        if cached is not None:
            return cached

    value = builder()
    if is_redis_available():
        cache_set(key, value, ttl_seconds)
    return value


def invalidate_dashboard() -> None:
    cache_delete(CacheKeys.dashboard_overview())
    cache_delete(CacheKeys.dashboard_security_summary())
    cache_delete_pattern("list:dashboard:*")


def invalidate_inventory() -> None:
    cache_delete(CacheKeys.stats_device_count())
    cache_delete(CacheKeys.stats_event_count())
    cache_delete_pattern("list:devices:*")
    cache_delete_pattern("list:events:*")
    invalidate_dashboard()


def invalidate_audit_summaries() -> None:
    cache_delete_pattern("list:audit:*")
    invalidate_dashboard()


def get_cached_stats_device_count(db_builder: Callable[[], int]) -> int:
    settings = get_settings()
    return get_or_set(
        CacheKeys.stats_device_count(),
        settings.cache_ttl_stats,
        db_builder,
    )


def get_or_set_model(
    key: str,
    ttl_seconds: int,
    builder: Callable[[], T],
    model: type[BaseModel],
) -> T:
    """Cache a Pydantic model by key."""
    return get_or_set(key, ttl_seconds, builder, model=model)


def get_cached_stats_event_count(db_builder: Callable[[], int]) -> int:
    settings = get_settings()
    return get_or_set(
        CacheKeys.stats_event_count(),
        settings.cache_ttl_stats,
        db_builder,
    )
