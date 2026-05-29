"""
Authentication routes: register, login (token), refresh, and protected user examples.
"""

import os
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from jwt.exceptions import InvalidTokenError
from sqlalchemy.orm import Session

from auth.jwt_handler import validate_refresh_token
from auth.login_lockout import (
    clear_login_attempts,
    is_locked_out,
    record_failed_login,
)
from auth.password_policy import validate_password_strength
from auth.security import authenticate_user, get_current_active_user, get_password_hash
from auth.token_service import issue_token_pair
from constants.audit_actions import AuditAction
from constants.roles import DEFAULT_ROLE
from core.limiter import limiter
from crud import user as user_crud
from database import get_db
from models.user import User
from schemas.user import Token, TokenRefreshRequest, UserCreate, UserResponse
from services.audit import log_audit
from utils.request import get_client_ip

router = APIRouter(tags=["auth"])

_LOGIN_LIMIT = os.getenv("RATE_LIMIT_LOGIN", "5/minute")
_REGISTER_LIMIT = os.getenv("RATE_LIMIT_REGISTER", "10/minute")
_REFRESH_LIMIT = os.getenv("RATE_LIMIT_REFRESH", "10/minute")


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(_REGISTER_LIMIT)
def register_user(
    request: Request,
    user_in: UserCreate,
    db: Session = Depends(get_db),
):
    """Create a new account. Password is hashed before storage."""
    if user_crud.get_user_by_username(db, user_in.username):
        raise HTTPException(status_code=400, detail="Username already registered")
    if user_crud.get_user_by_email(db, user_in.email):
        raise HTTPException(status_code=400, detail="Email already registered")

    validate_password_strength(user_in.password)
    hashed_password = get_password_hash(user_in.password)
    registration = user_in.model_copy(update={"role": DEFAULT_ROLE})
    return user_crud.create_user(db, registration, hashed_password)


@router.post("/token", response_model=Token)
@limiter.limit(_LOGIN_LIMIT)
async def login_for_access_token(
    request: Request,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db),
):
    """
    OAuth2 password flow (form fields: username, password).
    Returns short-lived access token + refresh token.

    Rate limited and lockout-protected against brute force.
    """
    ip = get_client_ip(request)
    username = form_data.username

    if is_locked_out(username, ip):
        log_audit(
            db,
            request,
            action=AuditAction.LOGIN_LOCKOUT,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            user_id=None,
            details=f"username_attempted={username}",
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed login attempts. Try again later.",
        )

    user = authenticate_user(db, username, form_data.password)
    if not user:
        failures = record_failed_login(username, ip)
        log_audit(
            db,
            request,
            action=AuditAction.LOGIN_FAILED,
            status_code=status.HTTP_401_UNAUTHORIZED,
            user_id=None,
            details=f"username_attempted={username} failures_in_window={failures}",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    clear_login_attempts(username, ip)
    log_audit(
        db,
        request,
        action=AuditAction.LOGIN_SUCCESS,
        status_code=status.HTTP_200_OK,
        user_id=user.id,
        details=f"username={user.username}",
    )
    return issue_token_pair(user.username)


@router.post("/token/refresh", response_model=Token)
@limiter.limit(_REFRESH_LIMIT)
async def refresh_access_token(
    request: Request,
    body: TokenRefreshRequest,
    db: Session = Depends(get_db),
):
    """
    Exchange a valid refresh token for a new access + refresh pair.

    Refresh tokens are long-lived but must not be used as Bearer on API routes.
    """
    try:
        username = validate_refresh_token(body.refresh_token)
    except InvalidTokenError:
        log_audit(
            db,
            request,
            action=AuditAction.INVALID_TOKEN,
            status_code=status.HTTP_401_UNAUTHORIZED,
            user_id=None,
            details="invalid_refresh_token",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    user = user_crud.get_user_by_username(db, username=username)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    tokens = issue_token_pair(user.username)
    log_audit(
        db,
        request,
        action=AuditAction.TOKEN_REFRESH,
        status_code=status.HTTP_200_OK,
        user_id=user.id,
        details=f"username={username}",
    )
    return tokens


@router.get("/users/me/", response_model=UserResponse)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    return current_user


@router.get("/users/me/items/")
async def read_own_items(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """Example protected route — replace with real device/ticket data later."""
    return [{"item_id": "Foo", "owner": current_user.username}]
