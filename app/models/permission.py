"""Permission model for RBAC system."""
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID, uuid4
from sqlalchemy import Text, DateTime, func, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from app.models.base import Base

class Permission(Base):
    __tablename__ = "permissions"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid4, 
        server_default=func.gen_random_uuid()
    )
    name: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    resource: Mapped[str] = mapped_column(Text, nullable=False)
    action: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc), 
        server_default=func.now()
    )

    roles: Mapped[List["Role"]] = relationship(
        "Role",
        secondary="role_permissions",
        back_populates="permissions"
    )

    __table_args__ = (
        Index("ix_permissions_name", "name", unique=True),
        Index("ix_permissions_category", "category"),
    )
