"""
Log each HTTP request with method, path, status, and duration.

Slow requests exceed SLOW_REQUEST_MS and are logged at WARNING level.
"""

import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from core.settings import get_settings

logger = logging.getLogger("nexventory.access")
perf_logger = logging.getLogger("nexventory.performance")

_SKIP_PATHS = {"/health", "/health/ready"}


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path in _SKIP_PATHS:
            return await call_next(request)

        start = time.perf_counter()
        status_code = 500
        slow_ms = get_settings().slow_request_ms
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        except Exception:
            logger.exception(
                "request_failed method=%s path=%s",
                request.method,
                request.url.path,
            )
            raise
        finally:
            duration_ms = (time.perf_counter() - start) * 1000
            log_msg = (
                "Request completed: %s %s — Duration: %.0fms (status=%s)"
                % (request.method, request.url.path, duration_ms, status_code)
            )
            if duration_ms >= slow_ms:
                perf_logger.warning("%s [slow]", log_msg)
            else:
                logger.info(log_msg)
