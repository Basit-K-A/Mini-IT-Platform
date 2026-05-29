"""
RBAC dependencies — authorization checks on top of JWT authentication.

Usage in a route:
    current_user: Annotated[User, Depends(require_any_role(Role.ADMIN, Role.ANALYST))]
"""

from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from auth.security import get_current_active_user
from constants.audit_actions import AuditAction
from constants.roles import ALLOWED_ROLES, ROLE_ADMIN, normalize_role
from database import get_db
from models.user import User
from services.audit import log_audit


def _deny_access(
    request: Request,
    db: Session,
    user: User,
    *,
    required_roles: tuple[str, ...],
    action: str = AuditAction.PERMISSION_DENIED,
) -> None:
    """
  Record a failed authorization attempt, then return 403 to the client.

  Separation of duties: authentication already succeeded; this is authorization failure.
  """
    effective = normalize_role(user.role)
    log_audit(
        db,
        request,
        action=action,
        status_code=status.HTTP_403_FORBIDDEN,
        user_id=user.id,
        details=(
            f"user_role={effective} required_roles={','.join(required_roles)} "
            f"endpoint={request.url.path}"
        ),
    )
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=f"Insufficient permissions. Required role(s): {', '.join(required_roles)}",
    )


def require_any_role(*allowed_roles: str) -> Callable:
    """
    Factory returning a FastAPI dependency that permits only listed roles.

    Admin always passes (full access). Others must match allowed_roles.
    """

    allowed = tuple(allowed_roles)

    async def checker(
        request: Request,
        db: Annotated[Session, Depends(get_db)],
        current_user: Annotated[User, Depends(get_current_active_user)],
    ) -> User:
        role = normalize_role(current_user.role)
        if role == ROLE_ADMIN:
            return current_user
        if role not in allowed:
            _deny_access(request, db, current_user, required_roles=allowed)
        return current_user

    return checker


def require_role(role: str) -> Callable:
    """Require exactly one role (admin still bypasses)."""
    if role not in ALLOWED_ROLES:
        raise ValueError(f"Unknown role: {role}")
    return require_any_role(role)
