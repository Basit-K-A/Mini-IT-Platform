"""
Read-only analytics queries for the security dashboard (audit logs, events, users).
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from constants.audit_actions import AuditAction
from models.audit_log import AuditLog
from models.device import Device
from models.event import Event
from models.user import User


def _since(hours: int) -> datetime:
    return datetime.now(timezone.utc) - timedelta(hours=hours)


def count_audit_action(db: Session, action: str, hours: int = 24) -> int:
    return (
        db.query(AuditLog)
        .filter(AuditLog.action == action, AuditLog.timestamp >= _since(hours))
        .count()
    )


def count_distinct_active_users(db: Session, hours: int = 24) -> int:
    return (
        db.query(func.count(func.distinct(AuditLog.user_id)))
        .filter(
            AuditLog.user_id.isnot(None),
            AuditLog.timestamp >= _since(hours),
        )
        .scalar()
        or 0
    )


def get_failed_logins_by_ip(db: Session, hours: int = 24, limit: int = 20) -> list[tuple]:
    """Returns rows: (ip_address, count, max_timestamp)."""
    return (
        db.query(
            AuditLog.ip_address,
            func.count(AuditLog.id),
            func.max(AuditLog.timestamp),
        )
        .filter(
            AuditLog.action == AuditAction.LOGIN_FAILED,
            AuditLog.timestamp >= _since(hours),
        )
        .group_by(AuditLog.ip_address)
        .order_by(func.count(AuditLog.id).desc())
        .limit(limit)
        .all()
    )


def get_usernames_for_failed_logins(
    db: Session, ip_address: str, hours: int = 24
) -> list[str]:
    rows = (
        db.query(AuditLog.details)
        .filter(
            AuditLog.action == AuditAction.LOGIN_FAILED,
            AuditLog.ip_address == ip_address,
            AuditLog.timestamp >= _since(hours),
        )
        .all()
    )
    names: set[str] = set()
    for (details,) in rows:
        if details and "username_attempted=" in details:
            part = details.split("username_attempted=", 1)[-1].split()[0]
            names.add(part)
    return sorted(names)


def get_top_active_users(db: Session, hours: int = 24, limit: int = 10) -> list[tuple]:
    """Returns (user_id, username, action_count)."""
    return (
        db.query(
            AuditLog.user_id,
            User.username,
            func.count(AuditLog.id),
        )
        .join(User, User.id == AuditLog.user_id)
        .filter(AuditLog.timestamp >= _since(hours), AuditLog.user_id.isnot(None))
        .group_by(AuditLog.user_id, User.username)
        .order_by(func.count(AuditLog.id).desc())
        .limit(limit)
        .all()
    )


def get_top_ip_addresses(db: Session, hours: int = 24, limit: int = 10) -> list[tuple]:
    return (
        db.query(AuditLog.ip_address, func.count(AuditLog.id))
        .filter(AuditLog.timestamp >= _since(hours))
        .group_by(AuditLog.ip_address)
        .order_by(func.count(AuditLog.id).desc())
        .limit(limit)
        .all()
    )


def count_audit_actions_grouped(db: Session, hours: int = 24) -> dict[str, int]:
    rows = (
        db.query(AuditLog.action, func.count(AuditLog.id))
        .filter(AuditLog.timestamp >= _since(hours))
        .group_by(AuditLog.action)
        .all()
    )
    return {action: count for action, count in rows}


def count_events_by_severity(db: Session, hours: int = 24) -> dict[str, int]:
    rows = (
        db.query(Event.severity, func.count(Event.id))
        .filter(Event.timestamp >= _since(hours))
        .group_by(Event.severity)
        .all()
    )
    return {sev: count for sev, count in rows}


def get_top_event_types(db: Session, hours: int = 24, limit: int = 5) -> list[tuple]:
    return (
        db.query(Event.event_type, func.count(Event.id))
        .filter(Event.timestamp >= _since(hours))
        .group_by(Event.event_type)
        .order_by(func.count(Event.id).desc())
        .limit(limit)
        .all()
    )


def count_permission_denied_by_ip(db: Session, ip: str, hours: int = 1) -> int:
    return (
        db.query(AuditLog)
        .filter(
            AuditLog.action == AuditAction.PERMISSION_DENIED,
            AuditLog.ip_address == ip,
            AuditLog.timestamp >= _since(hours),
        )
        .count()
    )


def count_failed_logins_by_ip(db: Session, ip: str, hours: int = 1) -> int:
    return (
        db.query(AuditLog)
        .filter(
            AuditLog.action == AuditAction.LOGIN_FAILED,
            AuditLog.ip_address == ip,
            AuditLog.timestamp >= _since(hours),
        )
        .count()
    )


def count_rate_limits_by_ip(db: Session, ip: str, hours: int = 1) -> int:
    return (
        db.query(AuditLog)
        .filter(
            AuditLog.action == AuditAction.RATE_LIMIT_EXCEEDED,
            AuditLog.ip_address == ip,
            AuditLog.timestamp >= _since(hours),
        )
        .count()
    )


def count_total_devices(db: Session) -> int:
    return db.query(Device).count()


def count_total_events(db: Session) -> int:
    return db.query(Event).count()


def get_recent_high_severity_events(db: Session, limit: int = 20) -> list[Event]:
    return (
        db.query(Event)
        .filter(Event.severity.in_(["high", "critical", "warning"]))
        .order_by(Event.timestamp.desc())
        .limit(limit)
        .all()
    )
