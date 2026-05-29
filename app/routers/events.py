"""
Event API routes — log entries tied to a device via device_id foreign key.

RBAC: read = any authenticated user; create = admin or technician.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from auth.roles import require_any_role
from auth.security import get_current_active_user
from constants.audit_actions import AuditAction
from constants.roles import ROLE_ADMIN, ROLE_TECHNICIAN
from crud import device as device_crud
from crud import event as event_crud
from database import get_db
from models.user import User
from schemas.event import EventCreate, EventResponse
from services.audit import log_audit

router = APIRouter(prefix="/events", tags=["events"])

RequireEventWrite = require_any_role(ROLE_ADMIN, ROLE_TECHNICIAN)


@router.post("", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
def create_event(
    event_in: EventCreate,
    request: Request,
    current_user: Annotated[User, Depends(RequireEventWrite)],
    db: Session = Depends(get_db),
):
    if not device_crud.get_device(db, event_in.device_id):
        raise HTTPException(status_code=404, detail="Device not found")
    event = event_crud.create_event(db, event_in)
    log_audit(
        db,
        request,
        action=AuditAction.EVENT_CREATED,
        status_code=status.HTTP_201_CREATED,
        user_id=current_user.id,
        details=(
            f"event_id={event.id} device_id={event.device_id} "
            f"type={event.event_type} severity={event.severity}"
        ),
    )
    return event


@router.get("", response_model=list[EventResponse])
def list_events(
    _current_user: Annotated[User, Depends(get_current_active_user)],
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
):
    """Read-only: all authenticated roles."""
    return event_crud.get_events(db, skip=skip, limit=limit)
