"""
Audit logging service — thin wrapper so routes stay small and logging stays consistent.
"""

from fastapi import Request
from sqlalchemy.orm import Session

from crud import audit as audit_crud
from utils.request import get_client_ip


def log_audit(
    db: Session,
    request: Request,
    *,
    action: str,
    status_code: int,
    user_id: int | None = None,
    details: str | None = None,
) -> None:
    """Record a security-relevant action with client IP and HTTP context."""
    audit_crud.create_audit_log(
        db,
        action=action,
        endpoint=request.url.path,
        ip_address=get_client_ip(request),
        status_code=status_code,
        user_id=user_id,
        details=details,
    )
