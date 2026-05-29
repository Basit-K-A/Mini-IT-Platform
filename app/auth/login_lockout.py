"""
In-memory failed-login tracking and temporary lockout.

Suitable for single-instance deployments (Docker Compose / one EC2 VM).
For multi-replica production, move counters to Redis.
"""

import os
import time
from collections import defaultdict
from threading import Lock

_lock = Lock()
# key: "username:ip" -> list of failure timestamps (epoch seconds)
_failures: dict[str, list[float]] = defaultdict(list)

MAX_ATTEMPTS = int(os.getenv("LOGIN_MAX_ATTEMPTS", "5"))
LOCKOUT_SECONDS = int(os.getenv("LOGIN_LOCKOUT_MINUTES", "15")) * 60
WINDOW_SECONDS = int(os.getenv("LOGIN_ATTEMPT_WINDOW_MINUTES", "15")) * 60


def _key(username: str, ip: str) -> str:
    return f"{username.lower()}:{ip}"


def _prune_old(timestamps: list[float], now: float) -> list[float]:
    cutoff = now - WINDOW_SECONDS
    return [t for t in timestamps if t >= cutoff]


def is_locked_out(username: str, ip: str) -> bool:
    """True if too many recent failures — block login attempts."""
    now = time.time()
    with _lock:
        key = _key(username, ip)
        recent = _prune_old(_failures.get(key, []), now)
        _failures[key] = recent
        return len(recent) >= MAX_ATTEMPTS


def record_failed_login(username: str, ip: str) -> int:
    """Record a failure; returns current failure count in the window."""
    now = time.time()
    with _lock:
        key = _key(username, ip)
        recent = _prune_old(_failures.get(key, []), now)
        recent.append(now)
        _failures[key] = recent
        return len(recent)


def clear_login_attempts(username: str, ip: str) -> None:
    """Clear failures after successful login."""
    with _lock:
        _failures.pop(_key(username, ip), None)
