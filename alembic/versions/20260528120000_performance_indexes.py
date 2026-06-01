"""
Performance indexes for audit, events, devices, and alerts.

Revision ID: 20260528120000
Revises:
Create Date: 2026-05-28

Why these indexes:
- audit_logs (action, timestamp): dashboard KPI counts and failed-login rollups
- audit_logs (user_id, timestamp): top active users
- audit_logs (ip_address, timestamp): brute-force / IP analytics
- events (device_id, timestamp): device event timelines
- events (severity, timestamp): severity dashboards
- devices (status, created_at): filtered inventory lists
- alerts (resolved, created_at): unresolved alert counts
"""

from typing import Sequence, Union

from alembic import op

revision: str = "20260528120000"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _create_index(name: str, table: str, columns: list[str]) -> None:
    op.create_index(name, table, columns, unique=False, if_not_exists=True)


def _drop_index(name: str, table: str) -> None:
    op.drop_index(name, table_name=table, if_exists=True)


def upgrade() -> None:
    _create_index("ix_audit_logs_action_timestamp", "audit_logs", ["action", "timestamp"])
    _create_index("ix_audit_logs_user_timestamp", "audit_logs", ["user_id", "timestamp"])
    _create_index("ix_audit_logs_ip_timestamp", "audit_logs", ["ip_address", "timestamp"])

    _create_index("ix_events_device_timestamp", "events", ["device_id", "timestamp"])
    _create_index("ix_events_severity_timestamp", "events", ["severity", "timestamp"])
    _create_index("ix_events_type_timestamp", "events", ["event_type", "timestamp"])

    _create_index("ix_devices_status_created", "devices", ["status", "created_at"])
    _create_index("ix_devices_department_status", "devices", ["department", "status"])
    _create_index("ix_devices_owner_status", "devices", ["owner_id", "status"])

    _create_index("ix_alerts_severity_created", "alerts", ["severity", "created_at"])
    _create_index("ix_alerts_resolved_created", "alerts", ["resolved", "created_at"])
    _create_index("ix_alerts_type_ip", "alerts", ["alert_type", "ip_address"])


def downgrade() -> None:
    for name, table in [
        ("ix_alerts_type_ip", "alerts"),
        ("ix_alerts_resolved_created", "alerts"),
        ("ix_alerts_severity_created", "alerts"),
        ("ix_devices_owner_status", "devices"),
        ("ix_devices_department_status", "devices"),
        ("ix_devices_status_created", "devices"),
        ("ix_events_type_timestamp", "events"),
        ("ix_events_severity_timestamp", "events"),
        ("ix_events_device_timestamp", "events"),
        ("ix_audit_logs_ip_timestamp", "audit_logs"),
        ("ix_audit_logs_user_timestamp", "audit_logs"),
        ("ix_audit_logs_action_timestamp", "audit_logs"),
    ]:
        _drop_index(name, table)
