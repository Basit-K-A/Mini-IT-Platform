"""
Pydantic schemas for Device API input/output.

from_attributes=True lets FastAPI read SQLAlchemy ORM objects (same as Pydantic v1 Config.orm_mode).
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from schemas.validators import DeviceStatus, validate_hostname, validate_ip_address


class DeviceCreate(BaseModel):
    hostname: str = Field(
        min_length=1,
        max_length=255,
        description="Unique host identifier (RFC 1123-style)",
    )
    ip_address: str = Field(min_length=1, max_length=45, description="IPv4 or IPv6")
    operating_system: str = Field(min_length=1, max_length=100)
    status: DeviceStatus = Field(
        default=DeviceStatus.active,
        description="Operational status",
    )
    department: str | None = Field(
        default=None,
        max_length=100,
        description="Organizational unit (e.g. IT, Finance)",
    )
    owner_id: int = Field(gt=0, description="User id responsible for this device")

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
    department: str | None = Field(default=None, max_length=100)
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
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "hostname": "srv-db-01",
                "ip_address": "10.0.1.15",
                "operating_system": "Ubuntu 22.04",
                "status": "active",
                "department": "IT",
                "owner_id": 2,
                "created_at": "2026-05-28T12:00:00Z",
            }
        },
    )

    id: int
    hostname: str
    ip_address: str
    operating_system: str
    status: str
    department: str | None = None
    owner_id: int
    created_at: datetime | None = None
