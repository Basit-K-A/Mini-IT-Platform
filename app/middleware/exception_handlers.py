"""
Centralized API error responses.

Goals:
- Never leak stack traces or SQL details to clients.
- Never return raw Python exception objects (they are not JSON serializable).
- One consistent error envelope for every failure (see core.errors).
- Full server-side logging for debugging.
"""

import logging
import os
from typing import Any

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from constants.audit_actions import AuditAction
from core.errors import code_for_status, error_payload
from database import SessionLocal
from services.audit import log_audit

logger = logging.getLogger(__name__)
_IS_PRODUCTION = os.getenv("ENVIRONMENT", "development").lower() == "production"


def _safe_message(message: str) -> str:
    """Hide internal details in production; show them in development."""
    if _IS_PRODUCTION:
        return "An error occurred processing your request"
    return message


def _sanitize_validation_errors(errors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Convert Pydantic validation errors into a JSON-serializable form.

    Root cause of "Object of type ValueError is not JSON serializable":
    when a custom field_validator raises ValueError, Pydantic v2 includes the raw
    exception inside each error's `ctx` (e.g. {"error": ValueError(...)}). JSONResponse
    cannot serialize that object, so we stringify `ctx` and drop the raw `input`.
    """
    cleaned: list[dict[str, Any]] = []
    for err in errors:
        item: dict[str, Any] = {
            "type": err.get("type"),
            "loc": [str(part) for part in err.get("loc", [])],
            "msg": err.get("msg"),
        }
        ctx = err.get("ctx")
        if ctx:
            item["ctx"] = {key: str(value) for key, value in ctx.items()}
        cleaned.append(item)
    return cleaned


async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """
    Handle intentionally raised HTTPExceptions (401/403/404/409/...).

    Returns the standardized envelope. `detail`/`message` carry the human message
    (e.g. "Forbidden") so clients depending on `detail` keep working.
    """
    detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
    code = code_for_status(exc.status_code)
    if exc.status_code >= 500:
        logger.error("HTTP %s on %s: %s", exc.status_code, request.url.path, detail)
    return JSONResponse(
        status_code=exc.status_code,
        content=error_payload(detail, code),
        headers=getattr(exc, "headers", None),
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """422 with a serializable error list (no raw ValueError objects)."""
    errors = [] if _IS_PRODUCTION else _sanitize_validation_errors(exc.errors())
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_payload(
            "Validation error",
            code_for_status(status.HTTP_422_UNPROCESSABLE_ENTITY),
            errors=errors,
        ),
    )


async def sqlalchemy_exception_handler(
    request: Request, exc: SQLAlchemyError
) -> JSONResponse:
    """Log the real database exception; return a safe message to the client."""
    # exc.__class__.__name__ + str(exc) gives the actual failure for debugging
    logger.exception(
        "Database error on %s %s: %s: %s",
        request.method,
        request.url.path,
        exc.__class__.__name__,
        exc,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_payload(
            _safe_message(f"{exc.__class__.__name__}: {exc}"),
            "DATABASE_ERROR",
        ),
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all: log full stack trace, never return the raw exception object."""
    logger.exception(
        "Unhandled %s on %s %s",
        exc.__class__.__name__,
        request.method,
        request.url.path,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_payload(
            _safe_message(f"{exc.__class__.__name__}: {exc}"),
            "INTERNAL_SERVER_ERROR",
        ),
    )


async def rate_limit_exception_handler(
    request: Request, exc: RateLimitExceeded
) -> JSONResponse:
    """429 response + audit trail for abuse detection."""
    db = SessionLocal()
    try:
        log_audit(
            db,
            request,
            action=AuditAction.RATE_LIMIT_EXCEEDED,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            user_id=None,
            details=f"limit={exc.detail}",
        )
    except Exception:
        logger.exception("Failed to write rate limit audit log")
        db.rollback()
    finally:
        db.close()

    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content=error_payload(
            "Rate limit exceeded. Please slow down and try again later.",
            "RATE_LIMIT_EXCEEDED",
        ),
        headers={"Retry-After": "60"},
    )


def register_exception_handlers(app) -> None:
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
    app.add_exception_handler(RateLimitExceeded, rate_limit_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
