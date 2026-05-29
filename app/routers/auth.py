"""
Authentication routes: register, login (token), and protected user examples.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from auth.jwt_handler import create_access_token
from constants.audit_actions import AuditAction
from crud import user as user_crud
from services.audit import log_audit
from auth.security import (
    access_token_expires,
    authenticate_user,
    get_current_active_user,
    get_password_hash,
)
from database import get_db
from models.user import User
from schemas.user import Token, UserCreate, UserResponse

router = APIRouter(tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user_in: UserCreate, db: Session = Depends(get_db)):
    """Create a new account. Password is hashed before storage."""
    if user_crud.get_user_by_username(db, user_in.username):
        raise HTTPException(status_code=400, detail="Username already registered")
    if user_crud.get_user_by_email(db, user_in.email):
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = get_password_hash(user_in.password)
    return user_crud.create_user(db, user_in, hashed_password)


@router.post("/token", response_model=Token)
async def login_for_access_token(
    request: Request,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db),
):
    """
    OAuth2 password flow (form fields: username, password).
    Returns a JWT bearer token used on protected routes.

    Successful and failed attempts are written to audit_logs (security monitoring).
    """
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        # Log even when username does not exist — supports brute-force detection
        log_audit(
            db,
            request,
            action=AuditAction.LOGIN_FAILED,
            status_code=status.HTTP_401_UNAUTHORIZED,
            user_id=None,
            details=f"username_attempted={form_data.username}",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    log_audit(
        db,
        request,
        action=AuditAction.LOGIN_SUCCESS,
        status_code=status.HTTP_200_OK,
        user_id=user.id,
        details=f"username={user.username}",
    )
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires(),
    )
    return Token(access_token=access_token, token_type="bearer")


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
