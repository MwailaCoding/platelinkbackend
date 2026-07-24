"""Role database model for RBAC."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Integer, Boolean, Enum as SQLEnum, ForeignKey, DateTime, UniqueConstraint, Uuid as UUID
from sqlalchemy.orm import relationship

from apps.api.app.models.base import Base
from apps.api.app.models.enums import RestaurantSize

class Role(Base):
    __tablename__ = "roles"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    restaurant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("restaurants.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    name = Column(
        String(100),
        nullable=False
    )
    description = Column(
        Text,
        nullable=True
    )
    level = Column(
        Integer,
        default=0,
        nullable=False
    )
    is_system = Column(
        Boolean,
        default=False,
        nullable=False
    )
    is_custom = Column(
        Boolean,
        default=False,
        nullable=False
    )
    restaurant_size = Column(
        SQLEnum(RestaurantSize, name="restaurantsize", create_type=False),
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

    restaurant = relationship("Restaurant", back_populates="roles")
    users = relationship("User", back_populates="role")
    permissions = relationship(
        "Permission",
        secondary="role_permissions",
        back_populates="roles",
        lazy="selectin"
    )

    __table_args__ = (
        UniqueConstraint("restaurant_id", "name", name="uq_roles_restaurant_name"),
    )
