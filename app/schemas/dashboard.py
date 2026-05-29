"""
Dashboard API responses — shaped for React cards, charts, and tables.
"""

from datetime import datetime

from pydantic import BaseModel, Field

from schemas.alert import AlertResponse
from schemas.audit_log import AuditLogResponse
from schemas.event import EventResponse


class DashboardOverview(BaseModel):
    failed_logins_24h: int
    successful_logins_24h: int
    permission_denied_24h: int
    rate_limit_events_24h: int
    critical_alerts: int
    high_alerts: int
    unresolved_alerts: int
    active_users_24h: int
    total_devices: int
    total_events: int
    security_events_24h: int
    new_alerts_generated: int = Field(
        description="Alerts created during this request's analysis pass",
    )


class SecuritySummary(BaseModel):
    events_by_severity: dict[str, int]
    alerts_by_severity: dict[str, int]
    top_event_types: list[dict[str, int | str]]
    audit_actions_24h: dict[str, int]


class FailedLoginEntry(BaseModel):
    ip_address: str
    attempt_count: int
    last_attempt: datetime | None
    usernames_attempted: list[str] = []


class UserActivityEntry(BaseModel):
    user_id: int
    username: str
    action_count: int


class IpActivityEntry(BaseModel):
    ip_address: str
    event_count: int


class DashboardRecentAlerts(BaseModel):
    alerts: list[AlertResponse]


class DashboardRecentAudit(BaseModel):
    audit_logs: list[AuditLogResponse]


class DashboardRecentEvents(BaseModel):
    events: list[EventResponse]
