"""
Pydantic schemas for Event API input/output.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class EventCreate(BaseModel):
    event_type: str = Field(min_length=1, max_length=100)
    severity: str = Field(min_length=1, max_length=50)
    message: str = Field(min_length=1)
    device_id: int
    # Optional: if omitted, the database default (now()) is used at insert time.
    timestamp: datetime | None = None


class EventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_type: str
    severity: str
    message: str
    timestamp: datetime
    device_id: int
