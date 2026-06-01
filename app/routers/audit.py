"""
Audit log API — read-only access to the security audit trail.

RBAC: admin and analyst only (technicians and viewers are denied).
"""

from typing import Annotated

import os

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from auth.roles import require_any_role
from constants.roles import ROLE_ADMIN, ROLE_ANALYST
from core.limiter import limiter
from crud import audit as audit_crud
from database import get_db
from dependencies.list_params import AuditLogListParams
from models.user import User
from schemas.audit_log import AuditLogResponse
from schemas.pagination import PaginatedResponse
from services.list_cache import cached_paginated_list

router = APIRouter(prefix="/audit-logs", tags=["audit"])

RequireAuditRead = require_any_role(ROLE_ADMIN, ROLE_ANALYST)

_AUDIT_READ_LIMIT = os.getenv("RATE_LIMIT_AUDIT", "30/minute")


@router.get(
    "",
    response_model=PaginatedResponse[AuditLogResponse],
    summary="List audit logs (paginated)",
)
@limiter.limit(_AUDIT_READ_LIMIT)
def list_audit_logs(
    request: Request,
    _current_user: Annotated[User, Depends(RequireAuditRead)],
    params: Annotated[AuditLogListParams, Depends()],
    db: Session = Depends(get_db),
):
    """
    Security audit trail with filters, sort, and pagination.

    **Filters**: `action`, `user_id`, `ip_address`, `status_code`, `endpoint_contains`

    Sensitive — admin and analyst roles only.
    """
    def _build() -> PaginatedResponse[AuditLogResponse]:
        items, meta = audit_crud.list_audit_logs(db, params)
        return PaginatedResponse(data=items, pagination=meta)

    return cached_paginated_list("audit", params, _build)
