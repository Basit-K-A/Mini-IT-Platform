"""
Reusable SQLAlchemy list helpers: pagination, whitelisted sorting, safe filtering.

Sorting uses a fixed allow-list of column attributes (never raw user strings in SQL),
which prevents injection via sort_by parameters.
"""

from __future__ import annotations

import math
from typing import Any, TypeVar

from sqlalchemy import asc, desc
from sqlalchemy.orm import Query, Session
from sqlalchemy.sql.elements import UnaryExpression

from schemas.pagination import PaginationMeta

# Shared limits for all list endpoints
DEFAULT_PAGE = 1
DEFAULT_LIMIT = 10
MAX_LIMIT = 100

ModelT = TypeVar("ModelT")


def normalize_page(page: int) -> int:
    return max(1, page)


def normalize_limit(limit: int) -> int:
    return min(MAX_LIMIT, max(1, limit))


def paginate(
    query: Query,
    *,
    page: int,
    limit: int,
) -> tuple[list[Any], PaginationMeta]:
    """
    Apply offset/limit and compute pagination metadata.

    Call after filters and sort are applied to the query.
    """
    page = normalize_page(page)
    limit = normalize_limit(limit)
    total_records = query.count()
    total_pages = max(1, math.ceil(total_records / limit)) if total_records else 1
    if page > total_pages and total_records > 0:
        page = total_pages

    offset = (page - 1) * limit
    items = query.offset(offset).limit(limit).all()

    meta = PaginationMeta(
        total_records=total_records,
        total_pages=total_pages,
        current_page=page,
        page_size=limit,
    )
    return items, meta


def apply_sort(
    query: Query,
    *,
    allowed_columns: dict[str, Any],
    sort_by: str | None,
    sort_order: str | None,
    default_column: Any,
    default_desc: bool = True,
) -> Query:
    """
    Order query by an allow-listed column name.

    Raises ValueError if sort_by is set but not in allowed_columns (map to HTTP 400 in routes).
    """
    order = (sort_order or "desc").lower()
    if order not in ("asc", "desc"):
        raise ValueError("sort_order must be 'asc' or 'desc'")

    if sort_by:
        if sort_by not in allowed_columns:
            allowed = ", ".join(sorted(allowed_columns))
            raise ValueError(f"sort_by must be one of: {allowed}")
        column = allowed_columns[sort_by]
    else:
        column = default_column

    clause: UnaryExpression = desc(column) if order == "desc" else asc(column)
    return query.order_by(clause)


def apply_exact_filters(query: Query, model: type[ModelT], filters: dict[str, Any]) -> Query:
    """
    Apply equality filters for non-empty values.

    Keys must match real SQLAlchemy column names on `model`.
    """
    for field, value in filters.items():
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        column = getattr(model, field, None)
        if column is None:
            continue
        query = query.filter(column == value)
    return query


def apply_ilike_filters(query: Query, model: type[ModelT], filters: dict[str, str | None]) -> Query:
    """Case-insensitive substring match (PostgreSQL ILIKE)."""
    for field, value in filters.items():
        if not value or not str(value).strip():
            continue
        column = getattr(model, field, None)
        if column is None:
            continue
        query = query.filter(column.ilike(f"%{value.strip()}%"))
    return query
