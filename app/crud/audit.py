"""
CRUD for audit_logs — append-only security event storage.
"""

from sqlalchemy.orm import Session

from models.audit_log import AuditLog


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
    db.commit()
    db.refresh(entry)
    return entry


def get_recent_audit_logs(db: Session, skip: int = 0, limit: int = 100) -> list[AuditLog]:
    """Newest-first audit trail for dashboards and investigations."""
    return (
        db.query(AuditLog)
        .order_by(AuditLog.timestamp.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
