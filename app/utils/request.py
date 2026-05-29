"""
HTTP request helpers for security logging.
"""

from fastapi import Request


def get_client_ip(request: Request) -> str:
    """
    Resolve the client IP for audit entries.

    Behind nginx, ProxyHeadersMiddleware exposes the real client via X-Forwarded-For.
    We take the first address in the list (original client).
    """
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client and request.client.host:
        return request.client.host
    return "unknown"
