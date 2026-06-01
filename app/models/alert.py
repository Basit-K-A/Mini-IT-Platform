"""
Security alerts — actionable findings from audit/event analysis (lightweight SIEM).
"""

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import relationship

from database import Base


class Alert(Base):
    __tablename__ = "alerts"
    __table_args__ = (
        Index("ix_alerts_severity_created", "severity", "created_at"),
        Index("ix_alerts_resolved_created", "resolved", "created_at"),
        Index("ix_alerts_type_ip", "alert_type", "ip_address"),
    )

    id = Column(Integer, primary_key=True, index=True)
    alert_type = Column(String(100), nullable=False, index=True)
    severity = Column(String(20), nullable=False, index=True)
    message = Column(Text, nullable=False)
    ip_address = Column(String(45), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    resolved = Column(Boolean, nullable=False, default=False, index=True)

    user = relationship("User", back_populates="alerts")
