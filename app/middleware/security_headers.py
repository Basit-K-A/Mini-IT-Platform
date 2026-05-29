"""
HTTP security headers — defense-in-depth for browser clients and API consumers.

These do not replace authentication; they reduce impact of XSS, clickjacking, and MIME sniffing.

IMPORTANT: Strict Content-Security-Policy breaks Swagger UI (/docs) because the UI loads
scripts and styles from CDNs (e.g. cdn.jsdelivr.net). Documentation paths use a relaxed CSP;
JSON API responses keep a strict policy.
"""

import os

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# Strict CSP for API JSON responses (not used for HTML documentation pages)
_STRICT_CSP = "default-src 'none'; frame-ancestors 'none'"

# Swagger/ReDoc need inline scripts + FastAPI/Swagger CDN assets
_DOCS_CSP = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
    "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
    "img-src 'self' data: https://fastapi.tiangolo.com; "
    "font-src 'self' https://cdn.jsdelivr.net; "
    "frame-ancestors 'self'"
)

_HSTS = os.getenv("SECURITY_HSTS", "max-age=31536000; includeSubDomains")

# OpenAPI/Swagger must stay public (no JWT) — only header policy differs here
_DOC_PATHS = frozenset({"/docs", "/redoc", "/openapi.json"})


def _is_documentation_path(path: str) -> bool:
    """FastAPI docs, ReDoc, OpenAPI schema, and their static subpaths."""
    if path in _DOC_PATHS:
        return True
    return path.startswith("/docs/") or path.startswith("/redoc/")


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        is_docs = _is_documentation_path(request.url.path)

        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault(
            "Permissions-Policy",
            "geolocation=(), microphone=(), camera=()",
        )

        if is_docs:
            # Allow Swagger UI to load; SAMEORIGIN is enough for docs (not DENY)
            response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
            response.headers.setdefault("Content-Security-Policy", _DOCS_CSP)
        else:
            response.headers.setdefault("X-Frame-Options", "DENY")
            response.headers.setdefault("Content-Security-Policy", _STRICT_CSP)

        if os.getenv("ENVIRONMENT", "development").lower() == "production":
            response.headers.setdefault("Strict-Transport-Security", _HSTS)

        return response
