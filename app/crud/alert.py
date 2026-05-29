"""
CRUD for security alerts.
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from constants.severity import SecuritySeverity
from models.alert import Alert


def create_alert(
    db: Session,
    *,
    alert_type: str,
    severity: SecuritySeverity,
    message: str,
    ip_address: str | None = None,
    user_id: int | None = None,
) -> Alert:
    alert = Alert(
        alert_type=alert_type,
        severity=severity.value,
        message=message,
        ip_address=ip_address,
        user_id=user_id,
        resolved=False,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


def get_recent_alerts(
    db: Session,
    skip: int = 0,
    limit: int = 50,
    unresolved_only: bool = False,
) -> list[Alert]:
    q = db.query(Alert).order_by(Alert.created_at.desc())
    if unresolved_only:
        q = q.filter(Alert.resolved.is_(False))
    return q.offset(skip).limit(limit).all()


def count_alerts_by_severity(
    db: Session,
    since: datetime | None = None,
    unresolved_only: bool = False,
) -> dict[str, int]:
    q = db.query(Alert.severity, func.count(Alert.id)).group_by(Alert.severity)
    if since:
        q = q.filter(Alert.created_at >= since)
    if unresolved_only:
        q = q.filter(Alert.resolved.is_(False))
    return {row[0]: row[1] for row in q.all()}


def count_unresolved_alerts(db: Session) -> int:
    return db.query(Alert).filter(Alert.resolved.is_(False)).count()


def alert_exists_recently(
    db: Session,
    *,
    alert_type: str,
    ip_address: str | None,
    within_minutes: int = 60,
) -> bool:
    """Avoid duplicate alerts for the same condition in a short window."""
    since = datetime.now(timezone.utc) - timedelta(minutes=within_minutes)
    q = db.query(Alert).filter(
        Alert.alert_type == alert_type,
        Alert.created_at >= since,
    )
    if ip_address:
        q = q.filter(Alert.ip_address == ip_address)
    return q.first() is not None
