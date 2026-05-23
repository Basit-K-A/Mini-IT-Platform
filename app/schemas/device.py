"""
Pydantic schemas for Device API input/output.

from_attributes=True lets FastAPI read SQLAlchemy ORM objects (same as Pydantic v1 Config.orm_mode).
"""

from pydantic import BaseModel, ConfigDict, Field


class DeviceCreate(BaseModel):
    hostname: str = Field(min_length=1, max_length=255)
    ip_address: str = Field(min_length=1, max_length=45)
    operating_system: str = Field(min_length=1, max_length=100)
    status: str = Field(default="active", max_length=50)
    owner_id: int


class DeviceUpdate(BaseModel):
    """Body for PUT /devices/{id} — full replacement of mutable fields."""

    hostname: str = Field(min_length=1, max_length=255)
    ip_address: str = Field(min_length=1, max_length=45)
    operating_system: str = Field(min_length=1, max_length=100)
    status: str = Field(max_length=50)
    owner_id: int


class DeviceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    hostname: str
    ip_address: str
    operating_system: str
    status: str
    owner_id: int
