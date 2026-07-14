# app/models/order.py
from datetime import datetime
from typing import List, Optional
from decimal import Decimal
from uuid import UUID, uuid4
from sqlalchemy import text, Text, Integer, Numeric, ForeignKey, func, DateTime, CheckConstraint, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, ENUM as PG_ENUM
from app.models.base import Base
from app.models.enums import OrderStatus, PaymentStatus, PaymentMethod

class Order(Base):
    __tablename__ = "orders"
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    restaurant_id: Mapped[UUID] = mapped_column(ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False)
    table_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("tables.id", ondelete="SET NULL"))
    session_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("customer_sessions.id", ondelete="CASCADE"))
    staff_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("staff.id", ondelete="SET NULL"))
    order_number: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    pacing_preference: Mapped[str] = mapped_column(Text, default="all_together")
    status: Mapped[OrderStatus] = mapped_column(PG_ENUM(OrderStatus, name="order_status_enum"), default=OrderStatus.received)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    tax: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    total: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    payment_status: Mapped[PaymentStatus] = mapped_column(PG_ENUM(PaymentStatus, name="payment_status_enum"), default=PaymentStatus.pending)
    payment_method: Mapped[Optional[PaymentMethod]] = mapped_column(PG_ENUM(PaymentMethod, name="payment_method_enum"))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    customer_phone: Mapped[Optional[str]] = mapped_column(Text)
    notes: Mapped[Optional[str]] = mapped_column(Text)  # was 'waiter_notes' in old model
    delivery_fee: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    customer_rating: Mapped[Optional[int]] = mapped_column(Integer)
    branch_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    restaurant: Mapped["Restaurant"] = relationship(back_populates="orders")
    table: Mapped["Table"] = relationship(back_populates="orders")
    session: Mapped["CustomerSession"] = relationship(back_populates="orders")
    staff: Mapped["Staff"] = relationship(back_populates="orders")
    items: Mapped[List["OrderItem"]] = relationship(back_populates="order", cascade="all, delete-orphan", lazy="selectin")
    payments: Mapped[List["Payment"]] = relationship(back_populates="order", lazy="selectin")

    @property
    def table_number(self) -> Optional[int]:
        return self.table.table_number if self.table else None


class OrderItem(Base):
    __tablename__ = "order_items"
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    order_id: Mapped[UUID] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    menu_item_id: Mapped[UUID] = mapped_column(ForeignKey("menu_items.id", ondelete="RESTRICT"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    special_instructions: Mapped[Optional[str]] = mapped_column(Text)
    
    # Course and Pacing
    course_number: Mapped[int] = mapped_column(Integer, default=1)
    course_name: Mapped[Optional[str]] = mapped_column(Text)
    is_fired: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    fired_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    status: Mapped[OrderStatus] = mapped_column(PG_ENUM(OrderStatus, name="order_status_enum"), default=OrderStatus.received)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    ready_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    estimated_start_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    estimated_ready_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    start_delay_seconds: Mapped[int] = mapped_column(Integer, default=0)
    
    # Hold functionality
    is_held: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    hold_reason: Mapped[Optional[str]] = mapped_column(Text)
    hold_resume_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    hold_started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    # Payment tracking
    is_paid: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True, default=False)
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    served_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    order: Mapped["Order"] = relationship(back_populates="items")
    modifiers: Mapped[List["OrderItemModifier"]] = relationship(back_populates="order_item", cascade="all, delete-orphan", lazy="selectin")
    menu_item: Mapped["MenuItem"] = relationship(lazy="selectin")

    @property
    def name(self) -> str:
        return self.menu_item.name if self.menu_item else "Dishes"

class OrderItemModifier(Base):
    __tablename__ = "order_item_modifiers"
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    restaurant_id: Mapped[UUID] = mapped_column(ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False)
    order_item_id: Mapped[UUID] = mapped_column(ForeignKey("order_items.id", ondelete="CASCADE"), nullable=False)
    modifier_id: Mapped[UUID] = mapped_column(ForeignKey("menu_item_modifiers.id", ondelete="RESTRICT"), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    
    order_item: Mapped["OrderItem"] = relationship(back_populates="modifiers")
