"""
CRUD helpers for Event — database access only, no HTTP logic.
"""

from sqlalchemy.orm import Session

from models.event import Event
from schemas.event import EventCreate


def get_event(db: Session, event_id: int) -> Event | None:
    return db.query(Event).filter(Event.id == event_id).first()


def get_events(db: Session, skip: int = 0, limit: int = 100) -> list[Event]:
    return db.query(Event).order_by(Event.timestamp.desc()).offset(skip).limit(limit).all()


def create_event(db: Session, event_in: EventCreate) -> Event:
    db_event = Event(
        event_type=event_in.event_type,
        severity=event_in.severity.value,
        message=event_in.message,
        device_id=event_in.device_id,
    )
    if event_in.timestamp is not None:
        db_event.timestamp = event_in.timestamp
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event
