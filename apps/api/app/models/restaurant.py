"""Restaurant model for multitenancy & multi-branch relationships."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, ForeignKey, Enum as SQLEnum, DateTime, Uuid as UUID
from sqlalchemy.orm import relationship

from apps.api.app.models.base import Base
from apps.api.app.models.enums import RestaurantSize

class Restaurant(Base):
    __tablename__ = "restaurants"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    name = Column(
        String(200),
        nullable=False
    )
    slug = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True
    )
    subdomain = Column(
        String(100),
        nullable=True,
        index=True
    )
    size = Column(
        SQLEnum(RestaurantSize, name="restaurantsize", create_type=False),
        default=RestaurantSize.SMALL,
        nullable=False
    )
    type = Column(
        String(50),
        default="casual_dining",
        nullable=False
    )
    is_multi_branch = Column(
        Boolean,
        default=False,
        nullable=False
    )
    parent_restaurant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("restaurants.id", ondelete="SET NULL"),
        nullable=True
    )
    logo_url = Column(
        String(255),
        nullable=True
    )
    primary_color = Column(
        String(7),
        default="#F97316",
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

    users = relationship("User", back_populates="restaurant", cascade="all, delete-orphan")
    roles = relationship("Role", back_populates="restaurant", cascade="all, delete-orphan")
    branches = relationship("Branch", back_populates="restaurant", cascade="all, delete-orphan", foreign_keys="Branch.restaurant_id")
