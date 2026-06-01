"""
CRUD helpers for User.

Keeps SQL/query logic out of routes and auth code so routes stay thin.
"""

from fastapi import HTTPException
from sqlalchemy.orm import Session

from core.query import apply_exact_filters, apply_ilike_filters, apply_sort, paginate
from dependencies.list_params import UserListParams
from models.user import User
from schemas.pagination import PaginationMeta
from schemas.user import UserCreate

_USER_SORT_COLUMNS = {
    "id": User.id,
    "username": User.username,
    "email": User.email,
    "role": User.role,
    "created_at": User.created_at,
    "is_active": User.is_active,
}


def get_user_by_username(db: Session, username: str) -> User | None:
    return db.query(User).filter(User.username == username).first()


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.query(User).filter(User.id == user_id).first()


def list_users(
    db: Session,
    params: UserListParams,
) -> tuple[list[User], PaginationMeta]:
    query = db.query(User)
    query = apply_exact_filters(
        query,
        User,
        {"role": params.role, "is_active": params.is_active},
    )
    query = apply_ilike_filters(
        query,
        User,
        {"username": params.username, "email": params.email},
    )

    try:
        query = apply_sort(
            query,
            allowed_columns=_USER_SORT_COLUMNS,
            sort_by=params.sort_by,
            sort_order=params.sort_order,
            default_column=User.created_at,
            default_desc=True,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return paginate(query, page=params.page, limit=params.limit)


def update_user_role(db: Session, user: User, role: str) -> User:
    user.role = role
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(user)
    return user


def create_user(db: Session, user_in: UserCreate, hashed_password: str) -> User:
    """Persist a new user. Password must already be hashed by the route layer."""
    db_user = User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=hashed_password,
        role=user_in.role,
        is_active=True,
    )
    db.add(db_user)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(db_user)
    return db_user
