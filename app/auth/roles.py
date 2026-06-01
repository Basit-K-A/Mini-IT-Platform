"""
RBAC dependencies — authorization checks on top of JWT authentication.

Usage in a route:
    current_user: Annotated[User, Depends(require_any_role(Role.ADMIN, Role.ANALYST))]
"""

from collections.abc import Callable, Iterable
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
    The client receives a generic "Forbidden"; the audit log keeps the full detail.
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
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


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


def require_role(roles: str | Iterable[str]) -> Callable:
    """
    Require one of the given role(s). Admin always bypasses.

    Accepts either a single role or a list/tuple of roles, e.g.:
        require_role("admin")
        require_role(["admin", "technician"])
    """
    if isinstance(roles, str):
        role_list = [roles]
    else:
        role_list = list(roles)

    unknown = [r for r in role_list if r not in ALLOWED_ROLES]
    if unknown:
        raise ValueError(f"Unknown role(s): {', '.join(unknown)}")

    return require_any_role(*role_list)
