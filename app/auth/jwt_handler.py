"""
JWT token creation, validation, and settings.

Access tokens: short-lived, sent on every API call.
Refresh tokens: longer-lived, used only at /token/refresh to obtain new access tokens.
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from jwt.exceptions import InvalidTokenError

from database import load_dotenv_files

load_dotenv_files()

SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "667868656f30710fb5c2d80e898e8d9e02684db92c1fbc0e27cd13f20ab84da3",
)
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

# Short-lived access token (minutes); refresh token (days)
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

TOKEN_TYPE_ACCESS = "access"
TOKEN_TYPE_REFRESH = "refresh"


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Signed JWT for API authorization (include typ=access)."""
    to_encode = data.copy()
    to_encode["typ"] = TOKEN_TYPE_ACCESS
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode["exp"] = expire
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(username: str) -> str:
    """Longer-lived token used only to mint new access tokens."""
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": username,
        "typ": TOKEN_TYPE_REFRESH,
        "exp": expire,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    """Decode and verify signature/expiry. Raises InvalidTokenError on failure."""
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])


def validate_access_token(token: str) -> str:
    """Return username from a valid access token."""
    payload = decode_token(token)
    if payload.get("typ") != TOKEN_TYPE_ACCESS:
        raise InvalidTokenError("Not an access token")
    username = payload.get("sub")
    if not username:
        raise InvalidTokenError("Missing subject")
    return username


def validate_refresh_token(token: str) -> str:
    """Return username from a valid refresh token."""
    payload = decode_token(token)
    if payload.get("typ") != TOKEN_TYPE_REFRESH:
        raise InvalidTokenError("Not a refresh token")
    username = payload.get("sub")
    if not username:
        raise InvalidTokenError("Missing subject")
    return username
