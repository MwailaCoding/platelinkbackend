"""Branch model for restaurant multi-location management."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Boolean, ForeignKey, DateTime, UniqueConstraint, Uuid as UUID
from sqlalchemy.orm import relationship

from apps.api.app.models.base import Base

class Branch(Base):
    __tablename__ = "branches"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    restaurant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("restaurants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    name = Column(
        String(100),
        nullable=False
    )
    address = Column(
        Text,
        nullable=True
    )
    city = Column(
        String(100),
        nullable=True
    )
    phone = Column(
        String(20),
        nullable=True
    )
    email = Column(
        String(255),
        nullable=True
    )
    manager_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    is_active = Column(
        Boolean,
        default=True,
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

    restaurant = relationship("Restaurant", back_populates="branches", foreign_keys=[restaurant_id])
    users = relationship("User", back_populates="branch", foreign_keys="User.branch_id")
    manager = relationship("User", foreign_keys=[manager_id])

    __table_args__ = (
        UniqueConstraint("restaurant_id", "name", name="uq_branches_restaurant_name"),
    )
