"""
Admin user management — list users and assign RBAC roles.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from auth.roles import require_role
from constants.audit_actions import AuditAction
from constants.roles import ROLE_ADMIN
from crud import user as user_crud
from database import get_db
from models.user import User
from schemas.user import UserResponse, UserRoleUpdate
from services.audit import log_audit

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserResponse])
def list_users(
    _admin: Annotated[User, Depends(require_role(ROLE_ADMIN))],
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
):
    """List all platform users. Admin only."""
    return user_crud.get_users(db, skip=skip, limit=limit)


@router.patch("/{user_id}/role", response_model=UserResponse)
def change_user_role(
    user_id: int,
    role_in: UserRoleUpdate,
    request: Request,
    admin: Annotated[User, Depends(require_role(ROLE_ADMIN))],
    db: Session = Depends(get_db),
):
    """Assign a new RBAC role to a user. Admin only."""
    target = user_crud.get_user_by_id(db, user_id)
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if target.id == admin.id and role_in.role != ROLE_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove your own admin role",
        )
    previous = target.role
    updated = user_crud.update_user_role(db, target, role_in.role)
    log_audit(
        db,
        request,
        action=AuditAction.ROLE_UPDATED,
        status_code=status.HTTP_200_OK,
        user_id=admin.id,
        details=(
            f"target_user_id={user_id} previous_role={previous} new_role={role_in.role}"
        ),
    )
    return updated
