"""
SlowAPI rate limiter — keyed by client IP (respects X-Forwarded-For behind nginx).
"""

import os

from slowapi import Limiter
from slowapi.util import get_remote_address

from utils.request import get_client_ip_for_limiter


def _rate_limit_key(request) -> str:
    return get_client_ip_for_limiter(request) or get_remote_address(request)


_DEFAULT = os.getenv("RATE_LIMIT_DEFAULT", "60/minute")

# Shared limiter instance; attach to app.state.limiter in main.py
limiter = Limiter(key_func=_rate_limit_key, default_limits=[_DEFAULT])
