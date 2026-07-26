"""Pydantic schemas for Cashier Terminal Turbo."""
from enum import Enum
from typing import Optional, List, Dict, Any
from uuid import UUID
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

# Enums
class PaymentMethod(str, Enum):
    CASH = "cash"
    MPESA = "mpesa"
    CARD = "card"
    MIXED = "mixed"
    SPLIT = "split"

class PaymentStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    VOIDED = "voided"

class ShiftStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"
    SUSPENDED = "suspended"

class ReceiptChannel(str, Enum):
    WHATSAPP = "whatsapp"
    SMS = "sms"
    EMAIL = "email"
    PRINT = "print"

class DrawerActionType(str, Enum):
    DROP = "drop"       # Safe cash drop
    PAYOUT = "payout"   # Petty cash payout
    FLOAT_IN = "float_in" # Additional float added

# Drawer Action Schemas
class DrawerActionRequest(BaseModel):
    shift_id: UUID
    action_type: DrawerActionType
    amount: Decimal
    reason: str

class DrawerActionResponse(BaseModel):
    id: UUID
    shift_id: UUID
    action_type: DrawerActionType
    amount: Decimal
    reason: str
    processed_by: Optional[UUID] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# Mixed Tender Payment Schemas
class MixedPaymentItem(BaseModel):
    method: PaymentMethod
    amount: Decimal
    phone_number: Optional[str] = None
    card_reference: Optional[str] = None
    cash_received: Optional[Decimal] = None

class MixedPaymentRequest(BaseModel):
    order_id: UUID
    payments: List[MixedPaymentItem]
    notes: Optional[str] = None

# Shift Schemas
class ShiftOpenRequest(BaseModel):
    terminal_id: str = "Terminal-1"
    opening_float: Decimal
    pin_code: Optional[str] = None
    notes: Optional[str] = None

class ShiftOpenResponse(BaseModel):
    id: UUID
    terminal_id: str
    cashier_id: UUID
    opening_float: Decimal
    opened_at: datetime
    status: ShiftStatus

    model_config = ConfigDict(from_attributes=True)

class ShiftCloseRequest(BaseModel):
    actual_cash: Decimal
    notes: Optional[str] = None

class ShiftCloseResponse(BaseModel):
    id: UUID
    terminal_id: str
    expected_cash: Decimal
    actual_cash: Decimal
    variance: Decimal
    closed_at: datetime
    cash_sales: Decimal
    mpesa_sales: Decimal
    card_sales: Decimal
    total_sales: Decimal

    model_config = ConfigDict(from_attributes=True)

class ShiftSummaryResponse(BaseModel):
    shift_id: UUID
    cashier_name: str
    terminal_id: str
    opened_at: datetime
    closed_at: Optional[datetime] = None
    opening_float: Decimal
    expected_cash: Decimal
    actual_cash: Optional[Decimal] = None
    variance: Optional[Decimal] = None
    cash_sales: Decimal
    mpesa_sales: Decimal
    card_sales: Decimal
    total_sales: Decimal
    transaction_count: int

# Payment Schemas
class MpesaPaymentRequest(BaseModel):
    order_id: UUID
    phone_number: str = Field(..., pattern=r"^07[0-9]{8}$|^01[0-9]{8}$|^254[0-9]{9}$")
    amount: Optional[Decimal] = None  # If not provided, use order total

class MpesaPaymentResponse(BaseModel):
    transaction_id: UUID
    order_id: UUID
    amount: Decimal
    status: PaymentStatus
    mpesa_receipt: Optional[str] = None
    phone_number: str
    merchant_request_id: str
    checkout_request_id: str

class CashPaymentRequest(BaseModel):
    order_id: UUID
    amount_received: Decimal
    notes: Optional[str] = None

class CashPaymentResponse(BaseModel):
    transaction_id: UUID
    order_id: UUID
    amount: Decimal
    cash_received: Decimal
    cash_change: Decimal
    status: PaymentStatus
    processed_at: datetime

    model_config = ConfigDict(from_attributes=True)

class CardPaymentRequest(BaseModel):
    order_id: UUID
    card_reference: str
    amount: Optional[Decimal] = None
    notes: Optional[str] = None

class CardPaymentResponse(BaseModel):
    transaction_id: UUID
    order_id: UUID
    amount: Decimal
    card_reference: str
    status: PaymentStatus
    processed_at: datetime

    model_config = ConfigDict(from_attributes=True)

class TransactionResponse(BaseModel):
    id: UUID
    order_id: UUID
    amount: Decimal
    method: PaymentMethod
    status: PaymentStatus
    reference: Optional[str] = None
    mpesa_receipt: Optional[str] = None
    card_reference: Optional[str] = None
    cash_received: Optional[Decimal] = None
    cash_change: Optional[Decimal] = None
    processed_by: UUID
    processed_at: datetime
    settled_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class TransactionListResponse(BaseModel):
    transactions: List[TransactionResponse]
    total: int
    page: int
    per_page: int

# Z-Report & X-Report Schemas
class ZReportResponse(BaseModel):
    shift_id: UUID
    generated_at: datetime
    summary: ShiftSummaryResponse
    transaction_breakdown: Dict[str, Any]
    payment_method_breakdown: Dict[str, Decimal]
    hourly_breakdown: List[Dict[str, Any]]
    status: str

class XReportResponse(BaseModel):
    shift_id: UUID
    generated_at: datetime
    opening_float: Decimal
    cash_sales: Decimal
    mpesa_sales: Decimal
    card_sales: Decimal
    total_sales: Decimal
    total_drops: Decimal
    total_payouts: Decimal
    total_float_in: Decimal
    expected_cash_on_hand: Decimal
    transaction_count: int
    drawer_actions: List[Dict[str, Any]]

# Receipt Schemas
class DigitalReceiptRequest(BaseModel):
    order_id: UUID
    channel: ReceiptChannel
    recipient: str  # Phone number or email
    message: Optional[str] = None

class DigitalReceiptResponse(BaseModel):
    id: UUID
    order_id: UUID
    receipt_url: str
    sent_via: ReceiptChannel
    sent_to: str
    sent_at: datetime
    is_delivered: bool
    delivered_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class MpesaConfirmRequest(BaseModel):
    merchant_request_id: str
    mpesa_receipt: str
    result_code: int = 0
