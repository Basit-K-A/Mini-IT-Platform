"""
Application roles for RBAC.

Authentication (JWT) proves who you are; authorization (role) decides what you may do.
"""

from typing import Final

# Supported roles — stored as strings in PostgreSQL for simplicity
ROLE_ADMIN: Final = "admin"
ROLE_ANALYST: Final = "analyst"
ROLE_TECHNICIAN: Final = "technician"
ROLE_VIEWER: Final = "viewer"

DEFAULT_ROLE: Final = ROLE_VIEWER

ALLOWED_ROLES: frozenset[str] = frozenset(
    {ROLE_ADMIN, ROLE_ANALYST, ROLE_TECHNICIAN, ROLE_VIEWER}
)

# Legacy registrations used role="user" — treat as viewer for permission checks
LEGACY_VIEWER_ALIASES: frozenset[str] = frozenset({"user", ROLE_VIEWER})


def normalize_role(role: str) -> str:
    """Map stored role to a known RBAC role (handles legacy values)."""
    if role in LEGACY_VIEWER_ALIASES:
        return ROLE_VIEWER
    if role in ALLOWED_ROLES:
        return role
    return role


def is_valid_role(role: str) -> bool:
    return role in ALLOWED_ROLES
