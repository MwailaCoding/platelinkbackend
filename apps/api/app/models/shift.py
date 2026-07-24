"""Staff shift and attendance database models."""
import uuid
from datetime import datetime, date, time, timezone
from sqlalchemy import Column, String, Date, Time, Text, ForeignKey, DateTime, Uuid as UUID
from sqlalchemy.orm import relationship

from apps.api.app.models.base import Base

class StaffShift(Base):
    __tablename__ = "staff_shifts"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    staff_id = Column(
        UUID(as_uuid=True),
        ForeignKey("staff.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    shift_date = Column(
        Date,
        nullable=False,
        index=True
    )
    start_time = Column(
        Time,
        nullable=False
    )
    end_time = Column(
        Time,
        nullable=False
    )
    break_start = Column(
        Time,
        nullable=True
    )
    break_end = Column(
        Time,
        nullable=True
    )
    status = Column(
        String(20),
        default="scheduled",
        nullable=False
    )
    notes = Column(
        Text,
        nullable=True
    )
    created_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
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

    staff = relationship("Staff", back_populates="shifts")
    attendances = relationship("StaffAttendance", back_populates="shift", cascade="all, delete-orphan")

class StaffAttendance(Base):
    __tablename__ = "staff_attendance"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    staff_id = Column(
        UUID(as_uuid=True),
        ForeignKey("staff.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    shift_id = Column(
        UUID(as_uuid=True),
        ForeignKey("staff_shifts.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    check_in = Column(
        DateTime(timezone=True),
        nullable=False
    )
    check_out = Column(
        DateTime(timezone=True),
        nullable=True
    )
    check_in_method = Column(
        String(20),
        nullable=False,
        default="pin"
    )
    check_out_method = Column(
        String(20),
        nullable=True
    )
    status = Column(
        String(20),
        default="present",
        nullable=False
    )
    notes = Column(
        Text,
        nullable=True
    )
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    staff = relationship("Staff", back_populates="attendance")
    shift = relationship("StaffShift", back_populates="attendances")
