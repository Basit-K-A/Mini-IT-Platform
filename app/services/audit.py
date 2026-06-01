"""
Audit logging service — sync or background persistence.

Routes should prefer schedule_audit_log() so responses return before DB commit.
"""

from fastapi import BackgroundTasks, Request
from sqlalchemy.orm import Session

from crud import audit as audit_crud
from services.background_tasks import AuditTaskPayload, schedule_audit_log
from utils.request import get_client_ip


def _payload_from_request(
    request: Request,
    *,
    action: str,
    status_code: int,
    user_id: int | None = None,
    details: str | None = None,
) -> AuditTaskPayload:
    return AuditTaskPayload(
        action=action,
        endpoint=request.url.path,
        ip_address=get_client_ip(request),
        status_code=status_code,
        user_id=user_id,
        details=details,
    )


def log_audit(
    db: Session,
    request: Request,
    *,
    action: str,
    status_code: int,
    user_id: int | None = None,
    details: str | None = None,
) -> None:
    """Synchronous audit write — use for security-critical paths that must commit before response."""
    audit_crud.create_audit_log(
        db,
        action=action,
        endpoint=request.url.path,
        ip_address=get_client_ip(request),
        status_code=status_code,
        user_id=user_id,
        details=details,
    )


def log_audit_background(
    background_tasks: BackgroundTasks,
    request: Request,
    *,
    action: str,
    status_code: int,
    user_id: int | None = None,
    details: str | None = None,
) -> None:
    """Defer audit log + cache invalidation until after the HTTP response."""
    schedule_audit_log(
        background_tasks,
        _payload_from_request(
            request,
            action=action,
            status_code=status_code,
            user_id=user_id,
            details=details,
        ),
    )
