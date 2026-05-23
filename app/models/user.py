"""
SQLAlchemy ORM model for the users table.

This describes how data is stored in PostgreSQL (columns, types, constraints).
It is NOT used directly as API request/response bodies — use Pydantic schemas for that.
"""

from sqlalchemy import Boolean, Column, DateTime, Integer, String, func
from sqlalchemy.orm import relationship

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="user")
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # One user can own many devices (SQLAlchemy relationship, not a DB column).
    devices = relationship("Device", back_populates="owner")
