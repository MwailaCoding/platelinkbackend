"""Cashier models for shift tracking, payment transactions, and digital receipts."""
from datetime import datetime, timezone
from typing import Optional, List
from uuid import UUID
from decimal import Decimal
from sqlalchemy import text, Text, Boolean, DateTime, Numeric, String, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from app.models.base import Base

class CashierShift(Base):
    __tablename__ = "cashier_shifts"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    terminal_id: Mapped[str] = mapped_column(String(20), nullable=False, default="Terminal-1")
    cashier_id: Mapped[UUID] = mapped_column(ForeignKey("staff.id", ondelete="RESTRICT"), nullable=False)
    opening_float: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    closing_float: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    expected_cash: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    actual_cash: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    variance: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="open", nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    cashier: Mapped["Staff"] = relationship("Staff", foreign_keys=[cashier_id], overlaps="shifts")
    transactions: Mapped[List["PaymentTransaction"]] = relationship("PaymentTransaction", back_populates="shift", cascade="all, delete-orphan")


class PaymentTransaction(Base):
    __tablename__ = "payment_transactions"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    order_id: Mapped[UUID] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    restaurant_id: Mapped[UUID] = mapped_column(ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False)
    branch_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("branches.id", ondelete="SET NULL"), nullable=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    method: Mapped[str] = mapped_column(String(20), nullable=False, default="cash")  # cash, mpesa, card, mixed, split
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")  # pending, completed, failed, refunded, voided
    reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    mpesa_receipt: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    mpesa_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    card_reference: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    cash_received: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    cash_change: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    processed_by: Mapped[UUID] = mapped_column(ForeignKey("staff.id", ondelete="RESTRICT"), nullable=False)
    shift_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("cashier_shifts.id", ondelete="SET NULL"), nullable=True)
    processed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    settled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    order: Mapped["Order"] = relationship("Order", overlaps="payment_transactions")
    restaurant: Mapped["Restaurant"] = relationship("Restaurant", overlaps="payment_transactions")
    branch: Mapped[Optional["Branches"]] = relationship("Branches", overlaps="payment_transactions")
    processor: Mapped["Staff"] = relationship("Staff", foreign_keys=[processed_by], overlaps="processed_transactions")
    shift: Mapped[Optional["CashierShift"]] = relationship("CashierShift", back_populates="transactions")


class DigitalReceipt(Base):
    __tablename__ = "digital_receipts"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    order_id: Mapped[UUID] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    receipt_url: Mapped[str] = mapped_column(String(255), nullable=False)
    sent_via: Mapped[str] = mapped_column(String(20), nullable=False, default="print")  # whatsapp, sms, email, print
    sent_to: Mapped[str] = mapped_column(String(255), nullable=False)
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    is_delivered: Mapped[bool] = mapped_column(Boolean, default=False)
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[UUID] = mapped_column(ForeignKey("staff.id", ondelete="RESTRICT"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    order: Mapped["Order"] = relationship("Order", overlaps="digital_receipts")
    creator: Mapped["Staff"] = relationship("Staff", foreign_keys=[created_by], overlaps="created_receipts")
