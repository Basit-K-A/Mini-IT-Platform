"""
Pydantic schemas for audit log API responses.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int | None
    action: str
    endpoint: str
    ip_address: str
    status_code: int
    timestamp: datetime
    details: str | None
