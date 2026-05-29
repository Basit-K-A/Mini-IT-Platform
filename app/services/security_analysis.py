"""
Security analysis engine — turns audit trails into alerts (lightweight SIEM correlation).

Runs rule-based detection (thresholds), not ML. Suitable for portfolio / single-tenant deployments.
"""

import os

from sqlalchemy.orm import Session

from constants.alert_types import AlertType
from constants.audit_actions import AuditAction
from constants.severity import SecuritySeverity
from crud import alert as alert_crud
from crud import audit as audit_crud
from crud import dashboard_queries as dash_q
# Configurable thresholds (tune via environment)
_FAILED_LOGIN_IP_THRESHOLD = int(os.getenv("ALERT_FAILED_LOGIN_IP_THRESHOLD", "5"))
_FAILED_LOGIN_WINDOW_HOURS = int(os.getenv("ALERT_FAILED_LOGIN_WINDOW_HOURS", "1"))
_PERMISSION_DENIED_THRESHOLD = int(os.getenv("ALERT_PERMISSION_DENIED_THRESHOLD", "5"))
_RATE_LIMIT_THRESHOLD = int(os.getenv("ALERT_RATE_LIMIT_THRESHOLD", "10"))
_ALERT_DEDUP_MINUTES = int(os.getenv("ALERT_DEDUP_MINUTES", "60"))


def _log_security_audit(
    db: Session,
    *,
    action: str,
    ip_address: str | None,
    user_id: int | None,
    details: str,
) -> None:
    """Internal audit entries for monitoring (no HTTP request context)."""
    audit_crud.create_audit_log(
        db,
        action=action,
        endpoint="/internal/security-analysis",
        ip_address=ip_address or "unknown",
        status_code=200,
        user_id=user_id,
        details=details,
    )


def _create_alert_if_new(
    db: Session,
    *,
    alert_type: str,
    severity: SecuritySeverity,
    message: str,
    ip_address: str | None = None,
    user_id: int | None = None,
    audit_action: str | None = None,
) -> bool:
    if alert_crud.alert_exists_recently(
        db, alert_type=alert_type, ip_address=ip_address, within_minutes=_ALERT_DEDUP_MINUTES
    ):
        return False
    alert_crud.create_alert(
        db,
        alert_type=alert_type,
        severity=severity,
        message=message,
        ip_address=ip_address,
        user_id=user_id,
    )
    _log_security_audit(
        db,
        action=audit_action or AuditAction.ALERT_CREATED,
        ip_address=ip_address,
        user_id=user_id,
        details=f"alert_type={alert_type} message={message[:200]}",
    )
    return True


def analyze_failed_logins(db: Session) -> int:
    """Detect brute-force patterns from failed login audit entries."""
    created = 0
    rows = dash_q.get_failed_logins_by_ip(db, hours=_FAILED_LOGIN_WINDOW_HOURS)
    for ip_address, count, _ in rows:
        if count < _FAILED_LOGIN_IP_THRESHOLD:
            continue
        severity = SecuritySeverity.CRITICAL if count >= _FAILED_LOGIN_IP_THRESHOLD * 2 else SecuritySeverity.HIGH
        alert_type = AlertType.POSSIBLE_BRUTE_FORCE
        message = (
            f"{count} failed login attempts from {ip_address} "
            f"in the last {_FAILED_LOGIN_WINDOW_HOURS} hour(s)"
        )
        if _create_alert_if_new(
            db,
            alert_type=alert_type,
            severity=severity,
            message=message,
            ip_address=ip_address,
            audit_action=AuditAction.BRUTE_FORCE_WARNING,
        ):
            _log_security_audit(
                db,
                action=AuditAction.SUSPICIOUS_ACTIVITY_DETECTED,
                ip_address=ip_address,
                user_id=None,
                details=message,
            )
            created += 1
    return created


def analyze_permission_denials(db: Session) -> int:
    created = 0
    for ip_address, _ in dash_q.get_top_ip_addresses(db, hours=1, limit=50):
        count = dash_q.count_permission_denied_by_ip(db, ip_address, hours=1)
        if count < _PERMISSION_DENIED_THRESHOLD:
            continue
        if _create_alert_if_new(
            db,
            alert_type=AlertType.REPEATED_PERMISSION_DENIED,
            severity=SecuritySeverity.HIGH,
            message=f"{count} permission denied responses from {ip_address} in the last hour",
            ip_address=ip_address,
        ):
            created += 1
    return created


def analyze_rate_limit_abuse(db: Session) -> int:
    created = 0
    for ip_address, _ in dash_q.get_top_ip_addresses(db, hours=1, limit=50):
        count = dash_q.count_rate_limits_by_ip(db, ip_address, hours=1)
        if count < _RATE_LIMIT_THRESHOLD:
            continue
        if _create_alert_if_new(
            db,
            alert_type=AlertType.EXCESSIVE_API_USAGE,
            severity=SecuritySeverity.MEDIUM,
            message=f"{count} rate-limit events from {ip_address} in the last hour",
            ip_address=ip_address,
        ):
            created += 1
    return created


def analyze_login_lockouts(db: Session) -> int:
    """LOGIN_LOCKOUT audit rows indicate active brute-force mitigation."""
    created = 0
    lockout_count = dash_q.count_audit_action(db, AuditAction.LOGIN_LOCKOUT, hours=24)
    if lockout_count < 1:
        return 0
    if _create_alert_if_new(
        db,
        alert_type=AlertType.SUSPICIOUS_AUTH_BEHAVIOR,
        severity=SecuritySeverity.HIGH,
        message=f"{lockout_count} account lockout(s) triggered in the last 24 hours",
        ip_address=None,
    ):
        created += 1
    return created


def analyze_high_severity_events(db: Session) -> int:
    created = 0
    for event in dash_q.get_recent_high_severity_events(db, limit=10):
        if event.severity.lower() != "critical":
            continue
        if _create_alert_if_new(
            db,
            alert_type=AlertType.HIGH_SEVERITY_EVENT,
            severity=SecuritySeverity.CRITICAL,
            message=f"Critical infrastructure event on device {event.device_id}: {event.message[:120]}",
            ip_address=None,
            user_id=None,
        ):
            created += 1
    return created


def run_security_analysis(db: Session) -> int:
    """
    Execute all detection rules. Call from dashboard endpoints before returning metrics.

    Returns the number of newly created alerts this pass.
    """
    total = 0
    total += analyze_failed_logins(db)
    total += analyze_permission_denials(db)
    total += analyze_rate_limit_abuse(db)
    total += analyze_login_lockouts(db)
    total += analyze_high_severity_events(db)
    return total
