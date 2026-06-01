"""
Per-request context for structured logging.

Holds the current request id and (when authenticated) the user id in
context variables so any log record produced during a request can be
enriched without threading these values through every function call.

These values are additive metadata only — they never change API behavior.
"""

from __future__ import annotations

import logging
from contextvars import ContextVar

# Populated by RequestLoggingMiddleware (request id) and the auth layer (user id).
request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)
user_id_var: ContextVar[int | None] = ContextVar("user_id", default=None)


def get_request_id() -> str | None:
    return request_id_var.get()


def get_user_id() -> int | None:
    return user_id_var.get()


def set_user_id(user_id: int | None) -> None:
    """Record the authenticated user id for the rest of the request."""
    user_id_var.set(user_id)


class ContextFilter(logging.Filter):
    """Inject request_id and user_id onto every LogRecord (None when absent)."""

    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "request_id"):
            record.request_id = request_id_var.get()
        if not hasattr(record, "user_id"):
            record.user_id = user_id_var.get()
        return True
