"""
Centralized API error responses — avoid leaking stack traces or SQL details to clients.
"""

import logging
import os

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from sqlalchemy.exc import SQLAlchemyError

from constants.audit_actions import AuditAction
from database import SessionLocal
from services.audit import log_audit

logger = logging.getLogger(__name__)
_IS_PRODUCTION = os.getenv("ENVIRONMENT", "development").lower() == "production"


def _safe_detail(message: str) -> str:
    if _IS_PRODUCTION:
        return "An error occurred processing your request"
    return message


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Return structured 422 without internal field paths in production."""
    if _IS_PRODUCTION:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": "Validation error", "errors": []},
        )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()},
    )


async def sqlalchemy_exception_handler(
    request: Request, exc: SQLAlchemyError
) -> JSONResponse:
    logger.exception("Database error on %s", request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": _safe_detail("Database error")},
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error on %s", request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": _safe_detail(str(exc))},
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
    finally:
        db.close()

    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "detail": "Rate limit exceeded. Please slow down and try again later.",
        },
        headers={"Retry-After": "60"},
    )


def register_exception_handlers(app) -> None:
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
    app.add_exception_handler(RateLimitExceeded, rate_limit_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
