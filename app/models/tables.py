# app/models/tables.py
from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4
from sqlalchemy import text, Text, Integer, ForeignKey, UniqueConstraint, CheckConstraint, func, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, ENUM as PG_ENUM, JSONB
from app.models.base import Base
from app.models.enums import TableStatus, SessionStatus

class Table(Base):
    __tablename__ = "tables"
    
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    restaurant_id: Mapped[UUID] = mapped_column(ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False)
    table_number: Mapped[int] = mapped_column(Integer, nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, default=1)
    location: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[TableStatus] = mapped_column(PG_ENUM(TableStatus, name="table_status_enum"), default=TableStatus.available)
    current_session_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True))
    occupied_since: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_status_change: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    status_history: Mapped[Optional[dict]] = mapped_column(JSONB, default=list)
    qr_code_url: Mapped[Optional[str]] = mapped_column(Text)
    qr_code_token: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    restaurant: Mapped["Restaurant"] = relationship(back_populates="tables")
    sessions: Mapped[List["CustomerSession"]] = relationship(back_populates="table")
    orders: Mapped[List["Order"]] = relationship(back_populates="table")
    calls: Mapped[List["WaiterCall"]] = relationship(back_populates="table")
    
    __table_args__ = (
        UniqueConstraint("restaurant_id", "table_number"),
        CheckConstraint("capacity > 0", name="tables_capacity_check"),
    )

class CustomerSession(Base):
    __tablename__ = "customer_sessions"
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    restaurant_id: Mapped[UUID] = mapped_column(ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False)
    table_id: Mapped[UUID] = mapped_column(ForeignKey("tables.id", ondelete="CASCADE"), nullable=False)
    session_token: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    customer_phone: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[SessionStatus] = mapped_column(PG_ENUM(SessionStatus, name="session_status_enum"), default=SessionStatus.active)
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    table: Mapped["Table"] = relationship(back_populates="sessions")
    orders: Mapped[List["Order"]] = relationship(back_populates="session")

class TableTransferLog(Base):
    __tablename__ = "table_transfer_logs"
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    restaurant_id: Mapped[UUID] = mapped_column(ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False)
    original_table_id: Mapped[UUID] = mapped_column(ForeignKey("tables.id", ondelete="CASCADE"), nullable=False)
    new_table_id: Mapped[UUID] = mapped_column(ForeignKey("tables.id", ondelete="CASCADE"), nullable=False)
    order_id: Mapped[UUID] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    transferred_by: Mapped[UUID] = mapped_column(ForeignKey("staff.id", ondelete="CASCADE"), nullable=False)
    transferred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class ItemTransferLog(Base):
    __tablename__ = "item_transfer_logs"
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    restaurant_id: Mapped[UUID] = mapped_column(ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False)
    order_item_id: Mapped[UUID] = mapped_column(ForeignKey("order_items.id", ondelete="CASCADE"), nullable=False)
    source_table_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("tables.id", ondelete="CASCADE"))
    target_table_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("tables.id", ondelete="CASCADE"))
    source_session_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("customer_sessions.id", ondelete="CASCADE"))
    target_session_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("customer_sessions.id", ondelete="CASCADE"))
    transferred_by: Mapped[UUID] = mapped_column(ForeignKey("staff.id", ondelete="CASCADE"), nullable=False)
    transferred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
