"""Branch model for multi-branch restaurant locations."""
from datetime import datetime
from typing import Optional, List
from uuid import UUID
from sqlalchemy import text, Text, Boolean, DateTime, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from app.models.base import Base

class Branch(Base):
    __tablename__ = "branches"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    restaurant_id: Mapped[UUID] = mapped_column(ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    city: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    email: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    manager_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("staff.id", ondelete="SET NULL"), nullable=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    restaurant: Mapped["Restaurant"] = relationship("Restaurant", back_populates="branches")
    manager: Mapped[Optional["Staff"]] = relationship("Staff", foreign_keys=[manager_id])
    staff: Mapped[List["Staff"]] = relationship("Staff", foreign_keys="Staff.branch_id", back_populates="branch")
