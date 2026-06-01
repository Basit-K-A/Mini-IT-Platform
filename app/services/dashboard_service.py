"""
Assemble dashboard DTOs from analytics queries (presentation layer for API routes).

Expensive aggregates are cached in Redis; overview uses batched SQL counts.
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from constants.audit_actions import AuditAction
from constants.severity import SecuritySeverity, normalize_event_severity
from core.settings import get_settings
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
from services.cache import get_or_set
from services.cache_keys import CacheKeys
from services.security_analysis import run_security_analysis


def _audit_count(batch: dict[str, int], action: str) -> int:
    return batch.get(action, 0)


def build_overview(db: Session, *, run_analysis: bool = True) -> DashboardOverview:
    # Always run correlation rules (may create alerts); cache only expensive aggregates.
    new_alerts = run_security_analysis(db) if run_analysis else 0
    settings = get_settings()
    key = CacheKeys.dashboard_overview()

    def _build() -> DashboardOverview:
        alert_counts = alert_crud.count_alerts_by_severity(db, unresolved_only=True)
        batch = dash_q.count_audit_actions_batch(db, hours=24)

        security_events = (
            _audit_count(batch, AuditAction.LOGIN_FAILED)
            + _audit_count(batch, AuditAction.PERMISSION_DENIED)
            + _audit_count(batch, AuditAction.INVALID_TOKEN)
        )

        return DashboardOverview(
            failed_logins_24h=_audit_count(batch, AuditAction.LOGIN_FAILED),
            successful_logins_24h=_audit_count(batch, AuditAction.LOGIN_SUCCESS),
            permission_denied_24h=_audit_count(batch, AuditAction.PERMISSION_DENIED),
            rate_limit_events_24h=_audit_count(batch, AuditAction.RATE_LIMIT_EXCEEDED),
            critical_alerts=alert_counts.get(SecuritySeverity.CRITICAL.value, 0),
            high_alerts=alert_counts.get(SecuritySeverity.HIGH.value, 0),
            unresolved_alerts=alert_crud.count_unresolved_alerts(db),
            active_users_24h=dash_q.count_distinct_active_users(db, hours=24),
            total_devices=dash_q.count_total_devices(db),
            total_events=dash_q.count_total_events(db),
            security_events_24h=security_events,
            new_alerts_generated=0,
        )

    overview = get_or_set(key, settings.cache_ttl_dashboard, _build, model=DashboardOverview)
    return overview.model_copy(update={"new_alerts_generated": new_alerts})


def build_security_summary(db: Session) -> SecuritySummary:
    settings = get_settings()
    key = CacheKeys.dashboard_security_summary()

    def _build() -> SecuritySummary:
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

    return get_or_set(key, settings.cache_ttl_dashboard, _build, model=SecuritySummary)


def build_failed_logins(db: Session, hours: int = 24) -> list[FailedLoginEntry]:
    enriched = dash_q.get_failed_logins_by_ip_enriched(db, hours=hours)
    return [
        FailedLoginEntry(
            ip_address=ip,
            attempt_count=count,
            last_attempt=last_ts,
            usernames_attempted=usernames,
        )
        for ip, count, last_ts, usernames in enriched
    ]


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
