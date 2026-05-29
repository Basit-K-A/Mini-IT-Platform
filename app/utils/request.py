"""
HTTP request helpers for security logging.
"""

from fastapi import Request


def get_client_ip_for_limiter(request) -> str:
    """IP for rate limiting (works with Starlette Request)."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def get_client_ip(request: Request) -> str:
    """Resolve the client IP for audit entries (same logic as rate limiting)."""
    return get_client_ip_for_limiter(request)
