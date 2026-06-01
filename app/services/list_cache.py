"""Cached paginated list responses for read-heavy endpoints."""

from collections.abc import Callable
from typing import TypeVar

from pydantic import BaseModel

from core.settings import get_settings
from schemas.pagination import PaginatedResponse
from services.cache import cache_get, cache_set, make_list_cache_key

T = TypeVar("T", bound=BaseModel)


def cached_paginated_list(
    resource: str,
    params: object,
    builder: Callable[[], PaginatedResponse[T]],
) -> PaginatedResponse[T]:
    """
    Return cached paginated JSON or execute builder and store result.

    Invalidated via cache_delete_pattern('list:devices:*') on writes.
    """
    settings = get_settings()
    key = make_list_cache_key(resource, params)
    raw = cache_get(key)
    if raw is not None:
        return PaginatedResponse.model_validate(raw)

    response = builder()
    cache_set(key, response.model_dump(), settings.cache_ttl_list)
    return response
