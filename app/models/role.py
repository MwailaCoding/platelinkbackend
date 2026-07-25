"""Role model for RBAC system."""
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID, uuid4
from sqlalchemy import Text, Integer, Boolean, DateTime, ForeignKey, UniqueConstraint, func, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from app.models.base import Base

class Role(Base):
    __tablename__ = "roles"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid4, 
        server_default=func.gen_random_uuid()
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    level: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_custom: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    restaurant_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("restaurants.id", ondelete="CASCADE"),
        nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc), 
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc), 
        onupdate=lambda: datetime.now(timezone.utc), 
        server_default=func.now()
    )

    restaurant: Mapped[Optional["Restaurant"]] = relationship(backref="roles")
    permissions: Mapped[List["Permission"]] = relationship(
        "Permission",
        secondary="role_permissions",
        back_populates="roles"
    )

    __table_args__ = (
        UniqueConstraint("restaurant_id", "name", name="uq_roles_restaurant_name"),
        Index("ix_roles_restaurant_id", "restaurant_id"),
        Index("ix_roles_name", "name"),
    )
