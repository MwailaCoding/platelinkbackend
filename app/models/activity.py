# app/models/activity.py
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4
from sqlalchemy import text, Text, ForeignKey, func, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from app.models.base import Base

class ActivityLog(Base):
    __tablename__ = "activity_logs"
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    restaurant_id: Mapped[UUID] = mapped_column(ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False)
    staff_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("staff.id", ondelete="SET NULL"))
    action: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_info: Mapped[Optional[dict]] = mapped_column(JSONB, name="metadata")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class WaiterCall(Base):
    __tablename__ = "waiter_calls"
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    restaurant_id: Mapped[UUID] = mapped_column(ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False)
    table_id: Mapped[UUID] = mapped_column(ForeignKey("tables.id", ondelete="CASCADE"), nullable=False)
    message: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, default="pending") # pending, acknowledged, completed
    acknowledged_by: Mapped[Optional[UUID]] = mapped_column(ForeignKey("staff.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    table: Mapped["Table"] = relationship(back_populates="calls")

    @property
    def table_number(self) -> Optional[int]:
        return self.table.table_number if self.table else None

