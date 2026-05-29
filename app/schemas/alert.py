"""
Pydantic schemas for security alerts.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from constants.severity import SecuritySeverity


class AlertResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    alert_type: str
    severity: str
    message: str
    ip_address: str | None
    user_id: int | None
    created_at: datetime
    resolved: bool


class AlertResolveUpdate(BaseModel):
    resolved: bool = True
