"""
Application-wide logging configuration.

Development: human-readable lines on stdout.
Production:  JSON lines on stdout (picked up by `docker logs` / CloudWatch later).
"""

import json
import logging
import os
import sys
from datetime import datetime, timezone

from core.request_context import ContextFilter

# Structured fields a log record may carry (set via logger `extra={...}`).
# Included in JSON output only when present and not None.
_CONTEXT_FIELDS = (
    "request_id",
    "user_id",
    "method",
    "endpoint",
    "action",
    "status",
    "duration_ms",
)


class JsonFormatter(logging.Formatter):
    """One JSON object per log line for parsers and monitoring tools."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for field in _CONTEXT_FIELDS:
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False, default=str)


def setup_logging() -> None:
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    environment = os.getenv("ENVIRONMENT", "development").lower()

    handler = logging.StreamHandler(sys.stdout)
    if environment == "production":
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s | %(levelname)-8s | %(name)s | "
                "req=%(request_id)s user=%(user_id)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )

    # Enrich every record with request_id / user_id from the request context.
    handler.addFilter(ContextFilter())

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)

    # Quieter third-party loggers in production
    if environment == "production":
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
