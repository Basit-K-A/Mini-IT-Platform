"""
HTTP security headers — defense-in-depth for browser clients and API consumers.

These do not replace authentication; they reduce impact of XSS, clickjacking, and MIME sniffing.
"""

import os

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# CSP for API-only responses (Swagger UI may need relax in dev — keep minimal default)
_DEFAULT_CSP = "default-src 'none'; frame-ancestors 'none'"
_HSTS = os.getenv("SECURITY_HSTS", "max-age=31536000; includeSubDomains")


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        # Clickjacking: prevent embedding in iframes
        response.headers.setdefault("X-Frame-Options", "DENY")
        # MIME sniffing: do not guess content type
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        # Leak less referrer data to third parties
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        # Restrict browser features (modern replacement for many X-* headers)
        response.headers.setdefault(
            "Permissions-Policy",
            "geolocation=(), microphone=(), camera=()",
        )
        response.headers.setdefault("Content-Security-Policy", _DEFAULT_CSP)

        # HSTS: force HTTPS in browsers (enable when TLS terminates in front of API)
        if os.getenv("ENVIRONMENT", "development").lower() == "production":
            response.headers.setdefault("Strict-Transport-Security", _HSTS)

        return response
