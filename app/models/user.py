"""User database model for RBAC."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, ForeignKey, Enum as SQLEnum, DateTime, Uuid as UUID
from sqlalchemy.orm import relationship

from apps.api.app.models.base import Base
from apps.api.app.models.enums import UserStatus

class User(Base):
    __tablename__ = "users"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    email = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True
    )
    phone = Column(
        String(20),
        nullable=True
    )
    password_hash = Column(
        String(255),
        nullable=False
    )
    first_name = Column(
        String(100),
        nullable=False
    )
    last_name = Column(
        String(100),
        nullable=False
    )
    role_id = Column(
        UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    restaurant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("restaurants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    branch_id = Column(
        UUID(as_uuid=True),
        ForeignKey("branches.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    pin = Column(
        String(4),
        nullable=True
    )
    status = Column(
        SQLEnum(UserStatus, name="userstatus", create_type=False),
        default=UserStatus.PENDING,
        nullable=False,
        index=True
    )
    last_login = Column(
        DateTime(timezone=True),
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

    role = relationship("Role", back_populates="users", lazy="selectin")
    restaurant = relationship("Restaurant", back_populates="users")
    branch = relationship("Branch", back_populates="users", foreign_keys=[branch_id])
    staff_profile = relationship("Staff", back_populates="user", uselist=False, cascade="all, delete-orphan")
