"""Unit tests for audit log creation and retrieval."""

from types import SimpleNamespace

import pytest

from constants.audit_actions import AuditAction
from crud import audit as audit_crud
from models.audit_log import AuditLog

pytestmark = pytest.mark.unit


def test_create_audit_log_persists(db_session):
    entry = audit_crud.create_audit_log(
        db_session,
        action=AuditAction.LOGIN_SUCCESS,
        endpoint="/token",
        ip_address="10.0.0.5",
        status_code=200,
        user_id=None,
        details="username=alice",
    )
    assert entry.id is not None
    assert entry.timestamp is not None  # server_default applied
    stored = db_session.query(AuditLog).filter(AuditLog.id == entry.id).one()
    assert stored.action == AuditAction.LOGIN_SUCCESS
    assert stored.endpoint == "/token"
    assert stored.status_code == 200


def test_create_audit_log_allows_null_user(db_session):
    entry = audit_crud.create_audit_log(
        db_session,
        action=AuditAction.LOGIN_FAILED,
        endpoint="/token",
        ip_address="10.0.0.6",
        status_code=401,
    )
    assert entry.user_id is None


def _audit_params(**overrides):
    base = {
        "page": 1,
        "limit": 50,
        "sort_by": None,
        "sort_order": "desc",
        "action": None,
        "user_id": None,
        "ip_address": None,
        "status_code": None,
        "endpoint_contains": None,
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def test_list_audit_logs_filter_by_action(db_session):
    for _ in range(3):
        audit_crud.create_audit_log(
            db_session, action=AuditAction.LOGIN_SUCCESS, endpoint="/token",
            ip_address="10.0.0.1", status_code=200,
        )
    audit_crud.create_audit_log(
        db_session, action=AuditAction.LOGIN_FAILED, endpoint="/token",
        ip_address="10.0.0.1", status_code=401,
    )

    items, meta = audit_crud.list_audit_logs(
        db_session, _audit_params(action=AuditAction.LOGIN_SUCCESS)
    )
    assert meta.total_records == 3
    assert all(log.action == AuditAction.LOGIN_SUCCESS for log in items)
