"""
Standardized API error envelope.

Every error response shares one shape so the frontend can handle errors uniformly:

    {
        "error": true,
        "message": "Human readable message",
        "code": "ERROR_CODE",
        "detail": "Human readable message"   # kept for backward compatibility
    }

`detail` mirrors `message` so existing clients that read `response.detail`
(including FastAPI's default behavior) keep working.
"""

from __future__ import annotations

from typing import Any

# HTTP status code -> stable machine-readable error code
STATUS_CODE_MAP: dict[int, str] = {
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    409: "CONFLICT",
    422: "VALIDATION_ERROR",
    429: "RATE_LIMIT_EXCEEDED",
    500: "INTERNAL_SERVER_ERROR",
    503: "SERVICE_UNAVAILABLE",
}


def code_for_status(status_code: int) -> str:
    return STATUS_CODE_MAP.get(status_code, f"HTTP_{status_code}")


def error_payload(
    message: str,
    code: str,
    *,
    errors: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build the standardized error body."""
    body: dict[str, Any] = {
        "error": True,
        "message": message,
        "code": code,
        # `detail` retained so older clients and FastAPI conventions still work
        "detail": message,
    }
    if errors is not None:
        body["errors"] = errors
    return body
