"""
Event API routes — log entries tied to a device via device_id foreign key.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from constants.audit_actions import AuditAction
from crud import device as device_crud
from crud import event as event_crud
from database import get_db
from schemas.event import EventCreate, EventResponse
from services.audit import log_audit

router = APIRouter(prefix="/events", tags=["events"])


@router.post("", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
def create_event(
    event_in: EventCreate,
    request: Request,
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
        user_id=None,
        details=(
            f"event_id={event.id} device_id={event.device_id} "
            f"type={event.event_type} severity={event.severity}"
        ),
    )
    return event


@router.get("", response_model=list[EventResponse])
def list_events(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return event_crud.get_events(db, skip=skip, limit=limit)
