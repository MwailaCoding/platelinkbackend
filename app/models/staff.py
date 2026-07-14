# app/models/staff.py
from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4
from sqlalchemy import text, Text, Boolean, DateTime, func, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, ENUM as PG_ENUM, JSONB
from app.models.base import Base
from app.models.enums import StaffRole, ShiftType

class Staff(Base):
    __tablename__ = "staff"
    
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    restaurant_id: Mapped[UUID] = mapped_column(ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False)
    full_name: Mapped[str] = mapped_column(Text, nullable=False)
    email: Mapped[Optional[str]] = mapped_column(Text)
    phone: Mapped[Optional[str]] = mapped_column(Text)
    role: Mapped[StaffRole] = mapped_column(PG_ENUM(StaffRole, name="staff_role_enum"), nullable=False)
    shift: Mapped[ShiftType] = mapped_column(PG_ENUM(ShiftType, name="shift_type_enum"), default=ShiftType.full)
    pin_code: Mapped[str] = mapped_column(Text, nullable=False)
    assigned_tables: Mapped[Optional[list]] = mapped_column(JSONB)
    kitchen_station: Mapped[Optional[str]] = mapped_column(Text)
    kitchen_station_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("kitchen_stations.id", ondelete="SET NULL"), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    branch_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    role_type: Mapped[Optional[str]] = mapped_column(Text)
    last_active_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    restaurant: Mapped["Restaurant"] = relationship(back_populates="staff")
    orders: Mapped[List["Order"]] = relationship(back_populates="staff")
    kitchen_station_rel: Mapped[Optional["KitchenStation"]] = relationship(back_populates="staff")

class StaffActivityLog(Base):
    __tablename__ = "staff_activity_logs"
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    staff_id: Mapped[UUID] = mapped_column(ForeignKey("staff.id", ondelete="CASCADE"), nullable=False)
    restaurant_id: Mapped[UUID] = mapped_column(ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False)
    clock_in_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    clock_out_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
