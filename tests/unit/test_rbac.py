"""Unit tests for RBAC permission checks (constants + role dependencies)."""

import asyncio

import pytest
from fastapi import HTTPException

from auth.roles import require_any_role, require_role
from constants.roles import (
    ROLE_ADMIN,
    ROLE_TECHNICIAN,
    ROLE_VIEWER,
    is_valid_role,
    normalize_role,
)
from models.audit_log import AuditLog

pytestmark = pytest.mark.unit


def test_normalize_role_handles_legacy_alias():
    assert normalize_role("user") == ROLE_VIEWER
    assert normalize_role(ROLE_ADMIN) == ROLE_ADMIN


def test_is_valid_role():
    assert is_valid_role(ROLE_ADMIN)
    assert not is_valid_role("superuser")


def test_require_role_rejects_unknown_role():
    with pytest.raises(ValueError):
        require_role("superuser")


def test_admin_bypasses_any_requirement(db_session, make_user, fake_request):
    admin = make_user(username="admin1", role=ROLE_ADMIN)
    checker = require_any_role(ROLE_TECHNICIAN)  # admin not listed, but bypasses
    result = asyncio.run(checker(fake_request("/devices"), db_session, admin))
    assert result is admin


def test_allowed_role_passes(db_session, make_user, fake_request):
    tech = make_user(username="tech1", role=ROLE_TECHNICIAN)
    checker = require_role([ROLE_ADMIN, ROLE_TECHNICIAN])
    result = asyncio.run(checker(fake_request("/devices"), db_session, tech))
    assert result is tech


def test_disallowed_role_denied_and_audited(db_session, make_user, fake_request):
    viewer = make_user(username="viewer1", role=ROLE_VIEWER)
    checker = require_role([ROLE_ADMIN, ROLE_TECHNICIAN])

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(checker(fake_request("/devices"), db_session, viewer))

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Forbidden"

    # Denial must be recorded in the audit trail.
    logs = db_session.query(AuditLog).filter(AuditLog.user_id == viewer.id).all()
    assert any(log.status_code == 403 for log in logs)
