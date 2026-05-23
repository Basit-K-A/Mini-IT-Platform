"""
SQLAlchemy model for device events (alerts, logs, status changes).

device_id links each event to exactly one device.
"""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from database import Base


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    severity = Column(String(50), nullable=False, index=True)
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False, index=True)

    device = relationship("Device", back_populates="events")
