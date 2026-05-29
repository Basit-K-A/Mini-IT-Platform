"""
Pydantic schemas for Device API input/output.

from_attributes=True lets FastAPI read SQLAlchemy ORM objects (same as Pydantic v1 Config.orm_mode).
"""

from pydantic import BaseModel, ConfigDict, Field, field_validator

from schemas.validators import DeviceStatus, validate_hostname, validate_ip_address


class DeviceCreate(BaseModel):
    hostname: str = Field(min_length=1, max_length=255)
    ip_address: str = Field(min_length=1, max_length=45)
    operating_system: str = Field(min_length=1, max_length=100)
    status: DeviceStatus = DeviceStatus.active
    owner_id: int = Field(gt=0)

    @field_validator("hostname")
    @classmethod
    def hostname_format(cls, value: str) -> str:
        return validate_hostname(value)

    @field_validator("ip_address")
    @classmethod
    def ip_format(cls, value: str) -> str:
        return validate_ip_address(value)


class DeviceUpdate(BaseModel):
    """Body for PUT /devices/{id} — full replacement of mutable fields."""

    hostname: str = Field(min_length=1, max_length=255)
    ip_address: str = Field(min_length=1, max_length=45)
    operating_system: str = Field(min_length=1, max_length=100)
    status: DeviceStatus
    owner_id: int = Field(gt=0)

    @field_validator("hostname")
    @classmethod
    def hostname_format(cls, value: str) -> str:
        return validate_hostname(value)

    @field_validator("ip_address")
    @classmethod
    def ip_format(cls, value: str) -> str:
        return validate_ip_address(value)


class DeviceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    hostname: str
    ip_address: str
    operating_system: str
    status: str
    owner_id: int
