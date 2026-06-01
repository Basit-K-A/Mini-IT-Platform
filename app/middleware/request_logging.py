"""
Log each HTTP request with method, path, status, and duration.

Also assigns a request id (honoring an inbound X-Request-ID when present),
exposes it on the response header, and binds it to the logging context so
every log line emitted during the request is correlated.

Slow requests exceed SLOW_REQUEST_MS and are logged at WARNING level.
"""

import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from core.request_context import request_id_var, user_id_var
from core.settings import get_settings

logger = logging.getLogger("nexventory.access")
perf_logger = logging.getLogger("nexventory.performance")

_SKIP_PATHS = {"/health", "/health/live", "/health/ready"}
_REQUEST_ID_HEADER = "X-Request-ID"


def _resolve_request_id(request: Request) -> str:
    """Reuse a caller-provided request id (trusted behind nginx) or mint one."""
    incoming = request.headers.get(_REQUEST_ID_HEADER)
    if incoming and len(incoming) <= 128:
        return incoming
    return uuid.uuid4().hex


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = _resolve_request_id(request)
        rid_token = request_id_var.set(request_id)
        uid_token = user_id_var.set(None)

        if request.url.path in _SKIP_PATHS:
            try:
                response = await call_next(request)
                response.headers[_REQUEST_ID_HEADER] = request_id
                return response
            finally:
                request_id_var.reset(rid_token)
                user_id_var.reset(uid_token)

        start = time.perf_counter()
        status_code = 500
        slow_ms = get_settings().slow_request_ms
        try:
            response = await call_next(request)
            status_code = response.status_code
            response.headers[_REQUEST_ID_HEADER] = request_id
            return response
        except Exception:
            logger.exception(
                "request_failed",
                extra={
                    "method": request.method,
                    "endpoint": request.url.path,
                    "action": "request_failed",
                },
            )
            raise
        finally:
            duration_ms = (time.perf_counter() - start) * 1000
            extra = {
                "method": request.method,
                "endpoint": request.url.path,
                "status": status_code,
                "duration_ms": round(duration_ms, 1),
                "action": "request_completed",
                "user_id": user_id_var.get(),
            }
            log_msg = (
                "Request completed: %s %s — Duration: %.0fms (status=%s)"
                % (request.method, request.url.path, duration_ms, status_code)
            )
            if duration_ms >= slow_ms:
                perf_logger.warning("%s [slow]", log_msg, extra=extra)
            else:
                logger.info(log_msg, extra=extra)
            request_id_var.reset(rid_token)
            user_id_var.reset(uid_token)
