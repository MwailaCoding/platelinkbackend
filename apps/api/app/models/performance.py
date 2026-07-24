"""Staff performance and review database models."""
import uuid
from datetime import datetime, date, timezone
from sqlalchemy import Column, String, Date, Float, Text, ForeignKey, DateTime, Index, Uuid as UUID
from sqlalchemy.orm import relationship

from apps.api.app.models.base import Base

class StaffPerformance(Base):
    __tablename__ = "staff_performance"

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
    period_start = Column(
        Date,
        nullable=False
    )
    period_end = Column(
        Date,
        nullable=False
    )
    metric_type = Column(
        String(50),
        nullable=False
    )
    metric_value = Column(
        Float,
        nullable=False
    )
    target_value = Column(
        Float,
        nullable=True
    )
    achieved_percentage = Column(
        Float,
        nullable=True
    )
    rating = Column(
        Float,
        nullable=True
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
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    staff = relationship("Staff", back_populates="performance")

class StaffReview(Base):
    __tablename__ = "staff_reviews"

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
    reviewer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    review_date = Column(
        Date,
        nullable=False
    )
    rating = Column(
        Float,
        nullable=False
    )
    strengths = Column(
        Text,
        nullable=True
    )
    improvements = Column(
        Text,
        nullable=True
    )
    goals = Column(
        Text,
        nullable=True
    )
    status = Column(
        String(20),
        default="draft",
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

    staff = relationship("Staff", back_populates="reviews")
