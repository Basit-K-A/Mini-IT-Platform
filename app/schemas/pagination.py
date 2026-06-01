"""
Standard paginated API envelope for list endpoints.

Frontend tables/charts can bind to `data` and drive paging UI from `pagination`.
"""

from collections.abc import Sequence
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class PaginationMeta(BaseModel):
    """Metadata for the current page of results."""

    total_records: int = Field(ge=0, description="Total rows matching filters (all pages)")
    total_pages: int = Field(ge=1, description="Number of pages at the current page_size")
    current_page: int = Field(ge=1, description="1-based page index")
    page_size: int = Field(ge=1, le=100, description="Rows per page (limit)")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic list response: items plus pagination block."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "data": [],
                "pagination": {
                    "total_records": 100,
                    "total_pages": 10,
                    "current_page": 1,
                    "page_size": 10,
                },
            }
        }
    )

    data: list[T]
    pagination: PaginationMeta


def paginated_response(
    items: Sequence[Any],
    meta: PaginationMeta,
    item_schema: type[T],
) -> PaginatedResponse[T]:
    """
    Build a paginated API envelope from ORM rows.

    List endpoints must not put SQLAlchemy models in ``data`` — FastAPI's
    ``response_model=PaginatedResponse[SomeSchema]`` validates each item and
    rejects ORM instances with ResponseValidationError.
    """
    return PaginatedResponse(
        data=[item_schema.model_validate(item) for item in items],
        pagination=meta,
    )
