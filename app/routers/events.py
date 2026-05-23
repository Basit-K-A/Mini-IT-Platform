"""
Event API routes — log entries tied to a device via device_id foreign key.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from crud import device as device_crud
from crud import event as event_crud
from database import get_db
from schemas.event import EventCreate, EventResponse

router = APIRouter(prefix="/events", tags=["events"])


@router.post("", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
def create_event(event_in: EventCreate, db: Session = Depends(get_db)):
    if not device_crud.get_device(db, event_in.device_id):
        raise HTTPException(status_code=404, detail="Device not found")
    return event_crud.create_event(db, event_in)


@router.get("", response_model=list[EventResponse])
def list_events(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return event_crud.get_events(db, skip=skip, limit=limit)
