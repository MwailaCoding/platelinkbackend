"""RolePermission junction table model."""
from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from app.models.base import Base

class RolePermission(Base):
    __tablename__ = "role_permissions"

    role_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), 
        ForeignKey("roles.id", ondelete="CASCADE"), 
        primary_key=True
    )
    permission_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), 
        ForeignKey("permissions.id", ondelete="CASCADE"), 
        primary_key=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc), 
        server_default=func.now()
    )

    role: Mapped["Role"] = relationship("Role", overlaps="permissions,roles")
    permission: Mapped["Permission"] = relationship("Permission", overlaps="permissions,roles")

