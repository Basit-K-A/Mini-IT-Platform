"""
Password hashing and FastAPI security dependencies.

Responsible for:
- bcrypt password verify/hash (passlib)
- OAuth2 bearer scheme
- authenticate_user()
- get_current_user / get_current_active_user dependencies
"""

from datetime import timedelta
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from auth.jwt_handler import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    validate_access_token,
)
from constants.audit_actions import AuditAction
from crud import user as user_crud
from database import get_db
from models.user import User
from services.audit import log_audit

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

_dummy_hash: str | None = None


def _get_dummy_hash() -> str:
    global _dummy_hash
    if _dummy_hash is None:
        _dummy_hash = pwd_context.hash("dummypassword")
    return _dummy_hash


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def authenticate_user(db: Session, username: str, password: str) -> User | None:
    user = user_crud.get_user_by_username(db, username=username)
    if not user:
        verify_password(password, _get_dummy_hash())
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


async def get_current_user(
    request: Request,
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        username = validate_access_token(token)
    except InvalidTokenError:
        log_audit(
            db,
            request,
            action=AuditAction.INVALID_TOKEN,
            status_code=status.HTTP_401_UNAUTHORIZED,
            user_id=None,
            details="invalid_or_expired_access_token",
        )
        raise credentials_exception

    user = user_crud.get_user_by_username(db, username=username)
    if user is None:
        log_audit(
            db,
            request,
            action=AuditAction.INVALID_TOKEN,
            status_code=status.HTTP_401_UNAUTHORIZED,
            user_id=None,
            details=f"unknown_subject={username}",
        )
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def access_token_expires() -> timedelta:
    return timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
