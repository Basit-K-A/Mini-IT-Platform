"""
Audit log API — read-only access to the security audit trail.
"""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from auth.security import get_current_active_user
from crud import audit as audit_crud
from database import get_db
from models.user import User
from schemas.audit_log import AuditLogResponse

router = APIRouter(prefix="/audit-logs", tags=["audit"])


@router.get("", response_model=list[AuditLogResponse])
def list_audit_logs(
    _current_user: Annotated[User, Depends(get_current_active_user)],
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
):
    """
    Return recent audit entries (newest first). Requires a valid JWT.

    In production you would restrict this to admin roles; authentication is
    required here so the audit trail is not publicly readable.
    """
    return audit_crud.get_recent_audit_logs(db, skip=skip, limit=limit)
