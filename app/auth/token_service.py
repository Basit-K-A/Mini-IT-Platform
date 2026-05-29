"""
Issue access + refresh token pairs for login and refresh flows.
"""

from auth.jwt_handler import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
    create_refresh_token,
)
from auth.security import access_token_expires
from schemas.user import Token


def issue_token_pair(username: str) -> Token:
    """Create a new access/refresh pair after successful authentication."""
    access = create_access_token(
        data={"sub": username},
        expires_delta=access_token_expires(),
    )
    refresh = create_refresh_token(username)
    return Token(
        access_token=access,
        refresh_token=refresh,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
