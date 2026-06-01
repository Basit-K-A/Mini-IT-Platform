"""
Pydantic schemas for audit log API responses.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "user_id": 2,
                "action": "LOGIN_SUCCESS",
                "endpoint": "/token",
                "ip_address": "127.0.0.1",
                "status_code": 200,
                "timestamp": "2026-05-28T12:00:00Z",
                "details": None,
            }
        },
    )

    id: int
    user_id: int | None
    action: str = Field(max_length=100)
    endpoint: str = Field(max_length=255)
    ip_address: str = Field(max_length=45)
    status_code: int = Field(ge=100, le=599)
    timestamp: datetime
    details: str | None = None
