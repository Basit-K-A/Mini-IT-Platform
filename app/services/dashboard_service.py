"""
Assemble dashboard DTOs from analytics queries (presentation layer for API routes).
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from constants.audit_actions import AuditAction
from constants.severity import SecuritySeverity, normalize_event_severity
from crud import alert as alert_crud
from crud import audit as audit_crud
from crud import dashboard_queries as dash_q
from schemas.dashboard import (
    DashboardOverview,
    FailedLoginEntry,
    IpActivityEntry,
    SecuritySummary,
    UserActivityEntry,
)
from services.security_analysis import run_security_analysis


def build_overview(db: Session, *, run_analysis: bool = True) -> DashboardOverview:
    new_alerts = run_security_analysis(db) if run_analysis else 0
    alert_counts = alert_crud.count_alerts_by_severity(db, unresolved_only=True)

    return DashboardOverview(
        failed_logins_24h=dash_q.count_audit_action(db, AuditAction.LOGIN_FAILED, hours=24),
        successful_logins_24h=dash_q.count_audit_action(db, AuditAction.LOGIN_SUCCESS, hours=24),
        permission_denied_24h=dash_q.count_audit_action(db, AuditAction.PERMISSION_DENIED, hours=24),
        rate_limit_events_24h=dash_q.count_audit_action(db, AuditAction.RATE_LIMIT_EXCEEDED, hours=24),
        critical_alerts=alert_counts.get(SecuritySeverity.CRITICAL.value, 0),
        high_alerts=alert_counts.get(SecuritySeverity.HIGH.value, 0),
        unresolved_alerts=alert_crud.count_unresolved_alerts(db),
        active_users_24h=dash_q.count_distinct_active_users(db, hours=24),
        total_devices=dash_q.count_total_devices(db),
        total_events=dash_q.count_total_events(db),
        security_events_24h=dash_q.count_audit_action(db, AuditAction.LOGIN_FAILED, hours=24)
        + dash_q.count_audit_action(db, AuditAction.PERMISSION_DENIED, hours=24)
        + dash_q.count_audit_action(db, AuditAction.INVALID_TOKEN, hours=24),
        new_alerts_generated=new_alerts,
    )


def build_security_summary(db: Session) -> SecuritySummary:
    raw_events = dash_q.count_events_by_severity(db, hours=24)
    events_by_severity: dict[str, int] = {
        SecuritySeverity.LOW.value: 0,
        SecuritySeverity.MEDIUM.value: 0,
        SecuritySeverity.HIGH.value: 0,
        SecuritySeverity.CRITICAL.value: 0,
    }
    for sev, count in raw_events.items():
        bucket = normalize_event_severity(sev).value
        events_by_severity[bucket] = events_by_severity.get(bucket, 0) + count

    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    alert_counts = alert_crud.count_alerts_by_severity(db, since=week_ago)
    alerts_by_severity = {
        SecuritySeverity.LOW.value: alert_counts.get(SecuritySeverity.LOW.value, 0),
        SecuritySeverity.MEDIUM.value: alert_counts.get(SecuritySeverity.MEDIUM.value, 0),
        SecuritySeverity.HIGH.value: alert_counts.get(SecuritySeverity.HIGH.value, 0),
        SecuritySeverity.CRITICAL.value: alert_counts.get(SecuritySeverity.CRITICAL.value, 0),
    }

    top_types = [
        {"event_type": et, "count": c}
        for et, c in dash_q.get_top_event_types(db, hours=24, limit=5)
    ]

    return SecuritySummary(
        events_by_severity=events_by_severity,
        alerts_by_severity=alerts_by_severity,
        top_event_types=top_types,
        audit_actions_24h=dash_q.count_audit_actions_grouped(db, hours=24),
    )


def build_failed_logins(db: Session, hours: int = 24) -> list[FailedLoginEntry]:
    entries = []
    for ip_address, count, last_ts in dash_q.get_failed_logins_by_ip(db, hours=hours):
        entries.append(
            FailedLoginEntry(
                ip_address=ip_address,
                attempt_count=count,
                last_attempt=last_ts,
                usernames_attempted=dash_q.get_usernames_for_failed_logins(db, ip_address, hours),
            )
        )
    return entries


def build_top_users(db: Session, hours: int = 24) -> list[UserActivityEntry]:
    return [
        UserActivityEntry(user_id=uid, username=uname, action_count=cnt)
        for uid, uname, cnt in dash_q.get_top_active_users(db, hours=hours)
    ]


def build_top_ips(db: Session, hours: int = 24) -> list[IpActivityEntry]:
    return [
        IpActivityEntry(ip_address=ip, event_count=cnt)
        for ip, cnt in dash_q.get_top_ip_addresses(db, hours=hours)
    ]


def get_recent_audit_logs(db: Session, limit: int = 50):
    return audit_crud.get_recent_audit_logs(db, limit=limit)
