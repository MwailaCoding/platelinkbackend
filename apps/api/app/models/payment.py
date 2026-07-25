# app/models/payment.py
from datetime import datetime
from typing import Optional
from decimal import Decimal
from uuid import UUID, uuid4
from sqlalchemy import text, Text, Integer, Numeric, ForeignKey, func, DateTime, ForeignKeyConstraint, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, ENUM as PG_ENUM
from app.models.base import Base
from app.models.enums import PaymentStatus, PaymentMethod

class Payment(Base):
    __tablename__ = "payments"
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    restaurant_id: Mapped[UUID] = mapped_column(ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False)
    order_id: Mapped[UUID] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    payment_method: Mapped[PaymentMethod] = mapped_column(PG_ENUM(PaymentMethod, name="payment_method_enum"), nullable=False)
    status: Mapped[PaymentStatus] = mapped_column(PG_ENUM(PaymentStatus, name="payment_status_enum"), default=PaymentStatus.pending)
    transaction_id: Mapped[Optional[str]] = mapped_column(Text)
    mpesa_receipt_number: Mapped[Optional[str]] = mapped_column(Text)
    mpesa_result_code: Mapped[Optional[int]] = mapped_column(Integer)
    mpesa_result_description: Mapped[Optional[str]] = mapped_column(Text)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    cash_received: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    change_given: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    cashier_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("staff.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    order: Mapped["Order"] = relationship(back_populates="payments")

    __table_args__ = (
        CheckConstraint("amount > 0", name="payments_amount_check"),
    )

class MpesaTransaction(Base):
    __tablename__ = "mpesa_transactions"
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    restaurant_id: Mapped[UUID] = mapped_column(ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False)
    checkout_request_id: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    merchant_request_id: Mapped[str] = mapped_column(Text, nullable=False)
    phone_number: Mapped[str] = mapped_column(Text, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    mpesa_receipt_number: Mapped[Optional[str]] = mapped_column(Text)
    result_code: Mapped[Optional[int]] = mapped_column(Integer)
    result_desc: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
