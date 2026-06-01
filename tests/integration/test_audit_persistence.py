"""Integration tests verifying audit log persistence through the API and DB."""

import pytest

from constants.audit_actions import AuditAction
from models.audit_log import AuditLog

pytestmark = pytest.mark.integration


def test_failed_login_writes_audit_row(client, make_user, db_session):
    make_user(username="alice", password="StrongP@ss1")
    resp = client.post("/token", data={"username": "alice", "password": "wrong"})
    assert resp.status_code == 401

    rows = (
        db_session.query(AuditLog)
        .filter(AuditLog.action == AuditAction.LOGIN_FAILED)
        .all()
    )
    assert len(rows) >= 1
    assert rows[0].endpoint == "/token"
    assert rows[0].status_code == 401


def test_successful_login_audited_and_readable_by_admin(client, make_user, auth_header):
    admin = make_user(username="admin", role="admin")
    # Successful login of the admin produces a LOGIN_SUCCESS audit entry.
    login = client.post("/token", data={"username": "admin", "password": "StrongP@ss1"})
    assert login.status_code == 200

    resp = client.get(
        "/audit-logs",
        params={"action": AuditAction.LOGIN_SUCCESS},
        headers=auth_header(admin.username),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["pagination"]["total_records"] >= 1
    assert all(row["action"] == AuditAction.LOGIN_SUCCESS for row in body["data"])


def test_audit_logs_denied_for_viewer(client, make_user, auth_header):
    viewer = make_user(username="viewer", role="viewer")
    resp = client.get("/audit-logs", headers=auth_header(viewer.username))
    assert resp.status_code == 403
