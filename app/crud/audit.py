"""
CRUD for audit_logs — append-only security event storage.
"""

from fastapi import HTTPException
from sqlalchemy.orm import Session

from core.query import apply_exact_filters, apply_ilike_filters, apply_sort, paginate
from dependencies.list_params import AuditLogListParams
from models.audit_log import AuditLog
from schemas.pagination import PaginationMeta

_AUDIT_SORT_COLUMNS = {
    "id": AuditLog.id,
    "timestamp": AuditLog.timestamp,
    "action": AuditLog.action,
    "user_id": AuditLog.user_id,
    "ip_address": AuditLog.ip_address,
    "status_code": AuditLog.status_code,
}


def create_audit_log(
    db: Session,
    *,
    action: str,
    endpoint: str,
    ip_address: str,
    status_code: int,
    user_id: int | None = None,
    details: str | None = None,
) -> AuditLog:
    """Persist one audit record. Commits immediately so it survives request failures."""
    entry = AuditLog(
        user_id=user_id,
        action=action,
        endpoint=endpoint,
        ip_address=ip_address,
        status_code=status_code,
        details=details,
    )
    db.add(entry)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(entry)
    return entry


def list_audit_logs(
    db: Session,
    params: AuditLogListParams,
) -> tuple[list[AuditLog], PaginationMeta]:
    """Filterable, sortable audit trail (newest first by default)."""
    query = db.query(AuditLog)
    query = apply_exact_filters(
        query,
        AuditLog,
        {
            "action": params.action,
            "user_id": params.user_id,
            "ip_address": params.ip_address,
            "status_code": params.status_code,
        },
    )
    query = apply_ilike_filters(
        query,
        AuditLog,
        {"endpoint": params.endpoint_contains},
    )

    try:
        query = apply_sort(
            query,
            allowed_columns=_AUDIT_SORT_COLUMNS,
            sort_by=params.sort_by,
            sort_order=params.sort_order,
            default_column=AuditLog.timestamp,
            default_desc=True,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return paginate(query, page=params.page, limit=params.limit)


def get_recent_audit_logs(db: Session, skip: int = 0, limit: int = 100) -> list[AuditLog]:
    """Legacy helper for dashboard — prefer list_audit_logs for API routes."""
    return (
        db.query(AuditLog)
        .order_by(AuditLog.timestamp.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
