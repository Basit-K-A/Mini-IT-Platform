"""
Audit log ORM model — immutable security trail of who did what, from where.

Audit logs support compliance and incident response: they are append-only in normal
operation (no update/delete routes in this phase).
"""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    # Nullable: failed logins and anonymous actions may have no authenticated user
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True)
    endpoint = Column(String(255), nullable=False)
    ip_address = Column(String(45), nullable=False)
    status_code = Column(Integer, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    details = Column(Text, nullable=True)

    user = relationship("User", back_populates="audit_logs")
