"""
JWT token creation and settings.

Keeps signing configuration in one place so routes do not touch SECRET_KEY directly.
"""

import os
from datetime import datetime, timedelta, timezone

import jwt

from database import load_dotenv_files

load_dotenv_files()

# Generate a production secret with: openssl rand -hex 32
SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "667868656f30710fb5c2d80e898e8d9e02684db92c1fbc0e27cd13f20ab84da3",
)
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Build a signed JWT. The 'sub' claim should hold the username."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
