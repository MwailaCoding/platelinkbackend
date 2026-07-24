"""Staff database model for employee management."""
import uuid
from datetime import datetime, date, timezone
from typing import List, Any
from sqlalchemy import Column, String, Date, Float, ForeignKey, DateTime, JSON, Uuid as UUID
from sqlalchemy.orm import relationship

from apps.api.app.models.base import Base

class Staff(Base):
    __tablename__ = "staff"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True
    )
    employee_id = Column(
        String(50),
        unique=True,
        nullable=True,
        index=True
    )
    department = Column(
        String(100),
        nullable=True
    )
    position = Column(
        String(100),
        nullable=True
    )
    hire_date = Column(
        Date,
        nullable=True
    )
    salary = Column(
        Float,
        nullable=True
    )
    shift_preferences = Column(
        JSON,
        default=list,
        nullable=False
    )
    skills = Column(
        JSON,
        default=list,
        nullable=False
    )
    certifications = Column(
        JSON,
        default=list,
        nullable=False
    )
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    user = relationship("User", back_populates="staff_profile", lazy="selectin")
    shifts = relationship("StaffShift", back_populates="staff", cascade="all, delete-orphan")
    attendance = relationship("StaffAttendance", back_populates="staff", cascade="all, delete-orphan")
    performance = relationship("StaffPerformance", back_populates="staff", cascade="all, delete-orphan")
    reviews = relationship("StaffReview", back_populates="staff", cascade="all, delete-orphan")
