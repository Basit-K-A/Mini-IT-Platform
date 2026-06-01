"""
SQLAlchemy model for managed IT devices.

owner_id is a foreign key to users.id — each device belongs to one user.
"""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from database import Base


class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    hostname = Column(String(255), nullable=False, index=True)
    ip_address = Column(String(45), nullable=False)
    operating_system = Column(String(100), nullable=False)
    status = Column(String(50), nullable=False, default="active")
    department = Column(String(100), nullable=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    owner = relationship("User", back_populates="devices")
    events = relationship(
        "Event",
        back_populates="device",
        cascade="all, delete-orphan",
    )
