"""
Security monitoring dashboard API — SIEM-style summaries for the React console.

RBAC: admin and analyst roles (same sensitivity as audit logs).
"""

import os
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from auth.roles import require_any_role
from constants.roles import ROLE_ADMIN, ROLE_ANALYST
from core.limiter import limiter
from crud import alert as alert_crud
from crud import event as event_crud
from database import get_db
from models.user import User
from schemas.alert import AlertResponse
from schemas.audit_log import AuditLogResponse
from schemas.dashboard import (
    DashboardOverview,
    DashboardRecentAlerts,
    DashboardRecentAudit,
    FailedLoginEntry,
    IpActivityEntry,
    SecuritySummary,
    UserActivityEntry,
)
from schemas.event import EventResponse
from services import dashboard_service as dash_svc
router = APIRouter(prefix="/dashboard", tags=["dashboard"])

RequireDashboardAccess = require_any_role(ROLE_ADMIN, ROLE_ANALYST)
_DASHBOARD_LIMIT = os.getenv("RATE_LIMIT_DASHBOARD", "60/minute")


@router.get("/overview", response_model=DashboardOverview)
@limiter.limit(_DASHBOARD_LIMIT)
def dashboard_overview(
    request: Request,
    _user: Annotated[User, Depends(RequireDashboardAccess)],
    db: Session = Depends(get_db),
):
    """
    High-level security KPIs for dashboard cards.

    Runs lightweight analysis rules before returning counts (may create new alerts).
    """
    return dash_svc.build_overview(db, run_analysis=True)


@router.get("/security-summary", response_model=SecuritySummary)
@limiter.limit(_DASHBOARD_LIMIT)
def security_summary(
    request: Request,
    _user: Annotated[User, Depends(RequireDashboardAccess)],
    db: Session = Depends(get_db),
):
    """Severity breakdowns and top event types for charts."""
    return dash_svc.build_security_summary(db)


@router.get("/recent-alerts", response_model=DashboardRecentAlerts)
@limiter.limit(_DASHBOARD_LIMIT)
def recent_alerts(
    request: Request,
    _user: Annotated[User, Depends(RequireDashboardAccess)],
    db: Session = Depends(get_db),
    limit: int = 50,
    unresolved_only: bool = False,
):
    alerts = alert_crud.get_recent_alerts(db, limit=limit, unresolved_only=unresolved_only)
    return DashboardRecentAlerts(alerts=alerts)


@router.get("/failed-logins", response_model=list[FailedLoginEntry])
@limiter.limit(_DASHBOARD_LIMIT)
def failed_logins(
    request: Request,
    _user: Annotated[User, Depends(RequireDashboardAccess)],
    db: Session = Depends(get_db),
    hours: int = 24,
):
    """Failed login attempts grouped by source IP (brute-force visibility)."""
    return dash_svc.build_failed_logins(db, hours=hours)


@router.get("/top-active-users", response_model=list[UserActivityEntry])
@limiter.limit(_DASHBOARD_LIMIT)
def top_active_users(
    request: Request,
    _user: Annotated[User, Depends(RequireDashboardAccess)],
    db: Session = Depends(get_db),
    hours: int = 24,
):
    return dash_svc.build_top_users(db, hours=hours)


@router.get("/top-ip-addresses", response_model=list[IpActivityEntry])
@limiter.limit(_DASHBOARD_LIMIT)
def top_ip_addresses(
    request: Request,
    _user: Annotated[User, Depends(RequireDashboardAccess)],
    db: Session = Depends(get_db),
    hours: int = 24,
):
    """IPs with the most audit activity — useful for spotting scanners."""
    return dash_svc.build_top_ips(db, hours=hours)


@router.get("/recent-audit-logs", response_model=DashboardRecentAudit)
@limiter.limit(_DASHBOARD_LIMIT)
def recent_audit_logs(
    request: Request,
    _user: Annotated[User, Depends(RequireDashboardAccess)],
    db: Session = Depends(get_db),
    limit: int = 50,
):
    logs = dash_svc.get_recent_audit_logs(db, limit=limit)
    return DashboardRecentAudit(audit_logs=logs)


@router.get("/recent-events", response_model=list[EventResponse])
@limiter.limit(_DASHBOARD_LIMIT)
def recent_security_events(
    request: Request,
    _user: Annotated[User, Depends(RequireDashboardAccess)],
    db: Session = Depends(get_db),
    limit: int = 50,
):
    """Recent infrastructure events (includes high/critical severities)."""
    from dependencies.list_params import EventListParams

    params = EventListParams(page=1, limit=min(limit, 100))
    items, _ = event_crud.list_events(db, params)
    return items
