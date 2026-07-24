"""Staff invitation database model."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Uuid as UUID
from sqlalchemy.orm import relationship

from apps.api.app.models.base import Base

class StaffInvitation(Base):
    __tablename__ = "staff_invitations"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    email = Column(
        String(255),
        nullable=False,
        index=True
    )
    restaurant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("restaurants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    role_id = Column(
        UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False
    )
    branch_id = Column(
        UUID(as_uuid=True),
        ForeignKey("branches.id", ondelete="SET NULL"),
        nullable=True
    )
    invited_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    token = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True
    )
    expires_at = Column(
        DateTime(timezone=True),
        nullable=False
    )
    accepted_at = Column(
        DateTime(timezone=True),
        nullable=True
    )
    status = Column(
        String(20),
        default="pending",
        nullable=False
    )
    message = Column(
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

    restaurant = relationship("Restaurant")
    role = relationship("Role")
    branch = relationship("Branch")
    inviter = relationship("User", foreign_keys=[invited_by])
