"""
Audit log API — read-only access to the security audit trail.

RBAC: admin and analyst only (technicians and viewers are denied).
"""

from typing import Annotated

import os

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from core.limiter import limiter

from auth.roles import require_any_role
from constants.roles import ROLE_ADMIN, ROLE_ANALYST
from crud import audit as audit_crud
from database import get_db
from models.user import User
from schemas.audit_log import AuditLogResponse

router = APIRouter(prefix="/audit-logs", tags=["audit"])

RequireAuditRead = require_any_role(ROLE_ADMIN, ROLE_ANALYST)


_AUDIT_READ_LIMIT = os.getenv("RATE_LIMIT_AUDIT", "30/minute")


@router.get("", response_model=list[AuditLogResponse])
@limiter.limit(_AUDIT_READ_LIMIT)
def list_audit_logs(
    request: Request,
    _current_user: Annotated[User, Depends(RequireAuditRead)],
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
):
    """
    Return recent audit entries (newest first).

    Sensitive security trail — not available to technician or viewer roles.
    """
    return audit_crud.get_recent_audit_logs(db, skip=skip, limit=limit)
