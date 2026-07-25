"""UserRole junction table model."""
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID
from sqlalchemy import DateTime, ForeignKey, func, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from app.models.base import Base

class UserRole(Base):
    __tablename__ = "user_roles"

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), 
        ForeignKey("staff.id", ondelete="CASCADE"), 
        primary_key=True
    )
    role_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), 
        ForeignKey("roles.id", ondelete="CASCADE"), 
        primary_key=True
    )
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc), 
        server_default=func.now()
    )
    assigned_by: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True), 
        ForeignKey("staff.id", ondelete="SET NULL"), 
        nullable=True
    )

    user: Mapped["Staff"] = relationship("Staff", foreign_keys=[user_id])
    role: Mapped["Role"] = relationship("Role")
    assigner: Mapped[Optional["Staff"]] = relationship("Staff", foreign_keys=[assigned_by])

    __table_args__ = (
        Index("ix_user_roles_user_id", "user_id"),
        Index("ix_user_roles_role_id", "role_id"),
    )
