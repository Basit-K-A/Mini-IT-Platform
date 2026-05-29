"""
Pydantic schemas for API validation and serialization.

Schemas define the shape of JSON going in and out of the API.
They are separate from SQLAlchemy models on purpose (see final explanation).
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from auth.password_policy import validate_password_strength
from constants.roles import ALLOWED_ROLES, DEFAULT_ROLE, is_valid_role


class UserCreate(BaseModel):
    """Body for POST /register."""

    username: str = Field(
        min_length=3,
        max_length=50,
        pattern=r"^[a-zA-Z0-9_\-]+$",
        description="Alphanumeric, underscore, hyphen only",
    )
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: str = DEFAULT_ROLE

    @field_validator("password")
    @classmethod
    def strong_password(cls, value: str) -> str:
        validate_password_strength(value)
        return value


class UserLogin(BaseModel):
    """
    Optional JSON login shape (OAuth2 /token still uses form fields).

    FastAPI's OAuth2PasswordRequestForm expects username + password as form data,
    which is what /token uses. This schema is useful for docs or future JSON login.
    """

    username: str
    password: str


class UserResponse(BaseModel):
    """Safe user data returned to clients (never includes hashed_password)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: EmailStr
    role: str
    is_active: bool
    created_at: datetime | None = None


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Access token lifetime in seconds")


class TokenRefreshRequest(BaseModel):
    """Body for POST /token/refresh."""

    refresh_token: str = Field(min_length=20, max_length=2048)


class TokenData(BaseModel):
    username: str | None = None


class UserRoleUpdate(BaseModel):
    """Admin-only body for PATCH /users/{id}/role."""

    role: str = Field(min_length=1, max_length=50)

    @field_validator("role")
    @classmethod
    def role_must_be_allowed(cls, value: str) -> str:
        if not is_valid_role(value):
            allowed = ", ".join(sorted(ALLOWED_ROLES))
            raise ValueError(f"role must be one of: {allowed}")
        return value
