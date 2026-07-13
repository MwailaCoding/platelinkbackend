# app/schemas/schemas.py
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from app.models import StaffRole, ShiftType, TableStatus, OrderStatus, PaymentStatus, PaymentMethod, CallStatus

# Auth
class Token(BaseModel):
    access_token: str
    token_type: str
    restaurant_id: UUID
    subdomain: str

class TokenData(BaseModel):
    staff_id: Optional[str] = None
    restaurant_id: Optional[str] = None
    role: Optional[str] = None

class UserRegister(BaseModel):
    restaurant_name: str
    subdomain: str
    owner_name: str
    email: EmailStr
    phone: str
    password: str
    restaurant_type: str = "single"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class StaffLogin(BaseModel):
    restaurant_id: Optional[UUID] = None
    restaurant_slug: Optional[str] = None
    pin_code: str

class QRLogin(BaseModel):
    qr_code: str

class VerifyEmail(BaseModel):
    email: EmailStr
    otp_code: Optional[str] = None
    code: Optional[str] = None

class RegisterResponse(BaseModel):
    success: bool
    message: str
    email: str

class ResendVerificationRequest(BaseModel):
    email: EmailStr

# Restaurant
class RestaurantBase(BaseModel):
    name: str
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    logo_url: Optional[str] = None

class RestaurantUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    logo_url: Optional[str] = None
    business_registration: Optional[str] = None
    kra_pin: Optional[str] = None

class RestaurantRead(RestaurantBase):
    id: UUID
    slug: str
    subdomain: str
    is_onboarded: bool
    business_registration: Optional[str] = None
    kra_pin: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

# Staff
class StaffBase(BaseModel):
    full_name: str
    role: StaffRole
    role_type: Optional[str] = 'waiter'
    branch_id: Optional[UUID] = None
    shift: ShiftType = ShiftType.full
    assigned_tables: Optional[List[int]] = None
    kitchen_station: Optional[str] = None
    kitchen_station_id: Optional[UUID] = None

class StaffCreate(StaffBase):
    pin_code: str

class BulkStaffInput(BaseModel):
    staff: List[StaffCreate]

class StaffUpdate(BaseModel):
    full_name: Optional[str] = None
    role: Optional[StaffRole] = None
    role_type: Optional[str] = None
    branch_id: Optional[UUID] = None
    shift: Optional[ShiftType] = None
    assigned_tables: Optional[List[int]] = None
    kitchen_station: Optional[str] = None
    kitchen_station_id: Optional[UUID] = None
    is_active: Optional[bool] = None


class StaffRead(StaffBase):
    id: UUID
    restaurant_id: UUID
    is_active: bool
    model_config = ConfigDict(from_attributes=True)

# Tables
class TableBase(BaseModel):
    table_number: int
    capacity: int = 1
    location: Optional[str] = None

class TableCreate(TableBase):
    pass

class TableStatusUpdate(BaseModel):
    status: TableStatus

class TableBulkCreate(BaseModel):
    start_number: int
    end_number: int
    capacity: int = 1
    location: Optional[str] = None

class TableRead(TableBase):
    id: UUID
    status: TableStatus
    qr_code_url: Optional[str] = None
    qr_code_token: Optional[str] = None
    current_session_id: Optional[UUID] = None
    occupied_since: Optional[datetime] = None
    last_status_change: Optional[datetime] = None
    status_history: Optional[List[Dict[str, Any]]] = None
    model_config = ConfigDict(from_attributes=True)

# Menu
class CategoryBase(BaseModel):
    name: str
    display_order: int = 0

class CategoryCreate(CategoryBase):
    pass

class CategoryRead(CategoryBase):
    id: UUID
    is_active: bool
    model_config = ConfigDict(from_attributes=True)

class ModifierBase(BaseModel):
    name: str
    price: Decimal
    is_available: bool = True

class ModifierCreate(ModifierBase):
    pass

class ModifierRead(ModifierBase):
    id: UUID
    model_config = ConfigDict(from_attributes=True)

class MenuItemBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: Decimal
    category_id: UUID
    image_url: Optional[str] = None
    preparation_time: int
    dietary_info: Optional[str] = None
    display_order: int = 0
    station_id: Optional[UUID] = None

class MenuItemCreate(MenuItemBase):
    pass


class MenuItemRead(MenuItemBase):
    id: UUID
    is_available: bool
    stock_quantity: Optional[int] = None
    modifiers: List[ModifierRead] = []
    model_config = ConfigDict(from_attributes=True)

# Customer
class SessionStart(BaseModel):
    qr_token: str

class OrderItemCreate(BaseModel):
    menu_item_id: UUID
    quantity: int
    special_instructions: Optional[str] = None
    modifier_ids: List[UUID] = []

class OrderCreate(BaseModel):
    items: List[OrderItemCreate]
    payment_method: PaymentMethod
    customer_phone: Optional[str] = None
    pacing_preference: Optional[str] = 'let_customer_choose'

class ChangePacingRequest(BaseModel):
    pacing: str

class CoursePacingSettings(BaseModel):
    default_pacing: str
    auto_fire_delay_minutes: int
    allow_mid_meal_change: bool = True

class WaiterCallCreate(BaseModel):
    message: Optional[str] = None

class WaiterCallRead(BaseModel):
    id: UUID
    restaurant_id: UUID
    table_id: UUID
    message: Optional[str] = None
    status: str
    acknowledged_by: Optional[UUID] = None
    created_at: datetime
    table_number: Optional[int] = None
    model_config = ConfigDict(from_attributes=True)

# Orders
class OrderItemRead(BaseModel):
    id: UUID
    menu_item_id: UUID
    name: Optional[str] = None
    quantity: int
    unit_price: Decimal
    subtotal: Decimal
    status: OrderStatus
    special_instructions: Optional[str] = None
    started_at: Optional[datetime] = None
    ready_at: Optional[datetime] = None
    station_id: Optional[UUID] = None
    model_config = ConfigDict(from_attributes=True)

class PaymentRead(BaseModel):
    id: UUID
    amount: Decimal
    payment_method: PaymentMethod
    status: PaymentStatus
    transaction_id: Optional[str] = None
    cash_received: Optional[Decimal] = None
    change_given: Optional[Decimal] = None
    completed_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class OrderRead(BaseModel):
    id: UUID
    order_number: str
    status: OrderStatus
    subtotal: Decimal
    tax: Decimal
    total: Decimal
    payment_status: PaymentStatus
    payment_method: Optional[PaymentMethod] = None
    items: List[OrderItemRead] = []
    payments: List[PaymentRead] = []
    created_at: datetime
    table_number: Optional[int] = None
    waiter_notes: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

# Analytics
class DashboardStats(BaseModel):
    today_sales: Decimal
    today_orders: int
    active_tables: int
    low_stock_count: int
    pending_orders: int

# Payments
class MpesaSTKPush(BaseModel):
    order_id: UUID
    phone_number: str
    amount: Decimal

class MpesaTestConnection(BaseModel):
    shortcode: str
    consumer_key: str
    consumer_secret: str
    passkey: str
    environment: str = "sandbox"

class CashConfirm(BaseModel):
    order_id: UUID

class TableTransferRequest(BaseModel):
    target_table_id: UUID

class ItemTransferRequest(BaseModel):
    item_ids: List[UUID]
    target_table_id: UUID
    target_session_id: Optional[UUID] = None

class SplitItem(BaseModel):
    customer_name: str
    item_ids: List[UUID]
    subtotal: Decimal

class SplitBillRequest(BaseModel):
    splits: List[SplitItem]

class OrderNotesRequest(BaseModel):
    note: str

# Import kitchen schemas
from app.schemas.kitchen import (
    KitchenStationBase, KitchenStationCreate, KitchenStationUpdate, KitchenStationRead,
    StationPrepTimeBase, StationPrepTimeCreate, StationPrepTimeUpdate, StationPrepTimeRead,
    KitchenRoutingRuleBase, KitchenRoutingRuleCreate, KitchenRoutingRuleRead,
    KitchenDisplaySettingBase, KitchenDisplaySettingCreate, KitchenDisplaySettingUpdate, KitchenDisplaySettingRead,
    KitchenPerformanceMetrics, AssignStationRequest, BulkAssignRequest, HoldRequest
)


