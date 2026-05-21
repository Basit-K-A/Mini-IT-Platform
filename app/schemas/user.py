"""
Pydantic schemas for API validation and serialization.

Schemas define the shape of JSON going in and out of the API.
They are separate from SQLAlchemy models on purpose (see final explanation).
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    """Body for POST /register."""

    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: str = "user"


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
    token_type: str


class TokenData(BaseModel):
    username: str | None = None
