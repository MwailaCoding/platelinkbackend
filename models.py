from datetime import datetime
from typing import List, Optional
from decimal import Decimal
from uuid import UUID, uuid4
import enum

from sqlalchemy import (text, 
    ForeignKey, Text, Boolean, Integer, Numeric, 
    DateTime, CheckConstraint, UniqueConstraint, func, ForeignKeyConstraint
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB, ENUM as PG_ENUM

class Base(DeclarativeBase):
    type_annotation_map = {
        dict: JSONB
    }

# --- Enums ---
class SubscriptionPlan(enum.Enum):
    starter = 'starter'
    pro = 'pro'
    enterprise = 'enterprise'

class StaffRole(enum.Enum):
    owner = 'owner'
    manager = 'manager'
    waiter = 'waiter'
    chef = 'chef'
    cashier = 'cashier'

class ShiftType(enum.Enum):
    morning = 'morning'
    afternoon = 'afternoon'
    evening = 'evening'
    night = 'night'
    full = 'full'

class TableStatus(enum.Enum):
    available = 'available'
    occupied = 'occupied'
    ordering = 'ordering'
    ordered = 'ordered'
    ready = 'ready'
    eating = 'eating'
    bill_requested = 'bill_requested'
    cleaning = 'cleaning'
    reserved = 'reserved'
    held = 'held'

class OrderStatus(enum.Enum):
    received = 'received'
    pending = 'pending'
    preparing = 'preparing'
    ready = 'ready'
    served = 'served'
    completed = 'completed'
    cancelled = 'cancelled'

class PaymentStatus(enum.Enum):
    pending = 'pending'
    paid = 'paid'
    failed = 'failed'
    refunded = 'refunded'
    partially_paid = 'partially_paid'

class PaymentMethod(enum.Enum):
    cash = 'cash'
    mpesa = 'mpesa'
    card = 'card'
    bank_transfer = 'bank_transfer'
    wallet = 'wallet'

class SubscriptionStatus(enum.Enum):
    trial = 'trial'
    active = 'active'
    suspended = 'suspended'
    cancelled = 'cancelled'

class CallType(enum.Enum):
    assistance = 'assistance'
    water = 'water'
    bill = 'bill'
    other = 'other'

class CallStatus(enum.Enum):
    pending = 'pending'
    acknowledged = 'acknowledged'
    completed = 'completed'

class SessionStatus(enum.Enum):
    active = 'active'
    closed = 'closed'
    expired = 'expired'

# --- Models ---

class Floors(Base):
    __tablename__ = "floors"
    
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    restaurant_id: Mapped[UUID] = mapped_column(ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    background_image_url: Mapped[Optional[str]] = mapped_column(Text)
    width: Mapped[int] = mapped_column(Integer, default=1200)
    height: Mapped[int] = mapped_column(Integer, default=800)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class FloorElements(Base):
    __tablename__ = "floor_elements"
    
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    floor_id: Mapped[UUID] = mapped_column(ForeignKey("floors.id", ondelete="CASCADE"), nullable=False)
    element_type: Mapped[str] = mapped_column(Text, nullable=False)
    element_data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Restaurant(Base):
    __tablename__ = "restaurants"
    
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    name: Mapped[str] = mapped_column(Text, nullable=False)
    slug: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    subdomain: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(Text)
    email: Mapped[Optional[str]] = mapped_column(Text)
    address: Mapped[Optional[str]] = mapped_column(Text)
    logo_url: Mapped[Optional[str]] = mapped_column(Text)
    subscription_plan: Mapped[SubscriptionPlan] = mapped_column(
        PG_ENUM(SubscriptionPlan, name="subscription_plan_enum"), default=SubscriptionPlan.starter
    )
    trial_ends_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    subscription_ends_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    prefix: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    business_registration: Mapped[Optional[str]] = mapped_column(Text)
    kra_pin: Mapped[Optional[str]] = mapped_column(Text)
    city: Mapped[Optional[str]] = mapped_column(Text)
    subscription_status: Mapped[SubscriptionStatus] = mapped_column(
        PG_ENUM(SubscriptionStatus, name="subscription_status_enum"), default=SubscriptionStatus.trial
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    deleted_by: Mapped[Optional[UUID]] = mapped_column(ForeignKey("staff.id", ondelete="SET NULL", use_alter=True, name="fk_restaurants_deleted_by"))
    parent_restaurant_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("restaurants.id"))
    restaurant_type: Mapped[str] = mapped_column(Text, default='single')
    is_multi_branch: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Branches(Base):
    __tablename__ = "branches"
    
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    restaurant_id: Mapped[UUID] = mapped_column(ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    address: Mapped[Optional[str]] = mapped_column(Text)
    city: Mapped[Optional[str]] = mapped_column(Text)
    phone: Mapped[Optional[str]] = mapped_column(Text)
    email: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_main: Mapped[bool] = mapped_column(Boolean, default=False)
    settings: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Staff(Base):
    __tablename__ = "staff"
    
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    restaurant_id: Mapped[UUID] = mapped_column(ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False)
    branch_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("branches.id"))
    full_name: Mapped[str] = mapped_column(Text, nullable=False)
    email: Mapped[Optional[str]] = mapped_column(Text)
    phone: Mapped[Optional[str]] = mapped_column(Text)
    role: Mapped[StaffRole] = mapped_column(PG_ENUM(StaffRole, name="staff_role_enum"), nullable=False)
    role_type: Mapped[str] = mapped_column(Text, default='waiter')
    shift: Mapped[ShiftType] = mapped_column(PG_ENUM(ShiftType, name="shift_type_enum"), default=ShiftType.full)
    pin_code: Mapped[str] = mapped_column(Text, nullable=False)
    assigned_tables: Mapped[Optional[dict]] = mapped_column(JSONB)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    last_active_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        CheckConstraint("pin_code ~ '^[0-9]{4}$'", name="staff_pin_format"),
    )

class Category(Base):
    __tablename__ = "categories"
    
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    restaurant_id: Mapped[UUID] = mapped_column(ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False)
    branch_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("branches.id"))
    name: Mapped[str] = mapped_column(Text, nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    description: Mapped[Optional[str]] = mapped_column(Text)
    image_url: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class MenuItem(Base):
    __tablename__ = "menu_items"
    
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    restaurant_id: Mapped[UUID] = mapped_column(ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False)
    branch_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("branches.id"))
    category_id: Mapped[UUID] = mapped_column(ForeignKey("categories.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    image_url: Mapped[Optional[str]] = mapped_column(Text)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)
    stock_quantity: Mapped[Optional[int]] = mapped_column(Integer)
    low_stock_threshold: Mapped[int] = mapped_column(Integer, default=5)
    dietary_info: Mapped[Optional[str]] = mapped_column(Text)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    preparation_time: Mapped[int] = mapped_column(Integer, default=15, server_default="15")
    calories: Mapped[Optional[int]] = mapped_column(Integer)
    is_vegetarian: Mapped[bool] = mapped_column(Boolean, default=False)
    is_spicy: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        CheckConstraint("preparation_time > 0", name="menu_items_prep_time_check"),
        CheckConstraint("price >= 0", name="menu_items_price_check_v2"),
        CheckConstraint("stock_quantity >= 0 OR stock_quantity IS NULL", name="menu_items_stock_check_v2"),
        CheckConstraint("calories >= 0", name="menu_items_calories_check"),
    )

class MenuItemModifier(Base):
    __tablename__ = "menu_item_modifiers"
    
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    restaurant_id: Mapped[UUID] = mapped_column(ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False)
    menu_item_id: Mapped[UUID] = mapped_column(ForeignKey("menu_items.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0.00)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        CheckConstraint("price >= 0", name="modifiers_price_check_v2"),
    )

class Table(Base):
    __tablename__ = "tables"
    
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    restaurant_id: Mapped[UUID] = mapped_column(ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False)
    branch_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("branches.id"))
    table_number: Mapped[int] = mapped_column(Integer, nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, default=1)
    location: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[TableStatus] = mapped_column(PG_ENUM(TableStatus, name="table_status_enum"), default=TableStatus.available)
    current_session_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True))
    occupied_since: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_status_change: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    status_history: Mapped[Optional[dict]] = mapped_column(JSONB, default=list)
    floor_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("floors.id", ondelete="SET NULL"))
    pos_x: Mapped[int] = mapped_column(Integer, default=0)
    pos_y: Mapped[int] = mapped_column(Integer, default=0)
    shape: Mapped[str] = mapped_column(Text, default='square')
    width: Mapped[int] = mapped_column(Integer, default=80)
    height: Mapped[int] = mapped_column(Integer, default=80)
    qr_code_url: Mapped[Optional[str]] = mapped_column(Text)
    qr_code_token: Mapped[Optional[str]] = mapped_column(Text)
    qr_code_printed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        UniqueConstraint("restaurant_id", "table_number"),
        CheckConstraint("capacity > 0", name="tables_capacity_check"),
    )

class CustomerSession(Base):
    __tablename__ = "customer_sessions"
    
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    restaurant_id: Mapped[UUID] = mapped_column(ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False)
    branch_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("branches.id"))
    table_id: Mapped[UUID] = mapped_column(ForeignKey("tables.id", ondelete="CASCADE"), nullable=False)
    session_token: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    customer_phone: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[SessionStatus] = mapped_column(
        PG_ENUM(SessionStatus, name="session_status_enum"), default=SessionStatus.active
    )
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Order(Base):
    __tablename__ = "orders"
    
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    restaurant_id: Mapped[UUID] = mapped_column(ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False)
    branch_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("branches.id"))
    table_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("tables.id", ondelete="SET NULL"))
    session_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("customer_sessions.id", ondelete="CASCADE"))
    staff_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("staff.id", ondelete="SET NULL"))
    order_number: Mapped[Optional[str]] = mapped_column(Text)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    customer_phone: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[OrderStatus] = mapped_column(PG_ENUM(OrderStatus, name="order_status_enum"), default=OrderStatus.received)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    tax: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    delivery_fee: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    total: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    payment_status: Mapped[PaymentStatus] = mapped_column(
        PG_ENUM(PaymentStatus, name="payment_status_enum"), default=PaymentStatus.pending
    )
    payment_method: Mapped[Optional[PaymentMethod]] = mapped_column(PG_ENUM(PaymentMethod, name="payment_method_enum"))
    customer_rating: Mapped[Optional[int]] = mapped_column(Integer)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        CheckConstraint("total >= 0", name="orders_total_check"),
        CheckConstraint("customer_rating BETWEEN 1 AND 5", name="orders_rating_check"),
    )

class OrderItem(Base):
    __tablename__ = "order_items"
    
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    order_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    order_created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    menu_item_id: Mapped[UUID] = mapped_column(ForeignKey("menu_items.id", ondelete="RESTRICT"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    special_instructions: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[OrderStatus] = mapped_column(PG_ENUM(OrderStatus, name="order_status_enum"), default=OrderStatus.received)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    ready_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    served_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    estimated_start_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    estimated_ready_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    start_delay_seconds: Mapped[int] = mapped_column(Integer, default=0)
    is_paid: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Hold functionality
    is_held: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    hold_reason: Mapped[Optional[str]] = mapped_column(Text)
    hold_resume_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    hold_started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        ForeignKeyConstraint(
            ["order_id", "order_created_at"],
            ["orders.id", "orders.created_at"],
            ondelete="CASCADE"
        ),
        CheckConstraint("quantity > 0", name="order_items_qty_check"),
        CheckConstraint("unit_price >= 0", name="order_items_price_check_v2"),
        CheckConstraint("subtotal >= 0", name="order_items_subtotal_check_v2"),
    )

class OrderItemModifier(Base):
    __tablename__ = "order_item_modifiers"
    
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    restaurant_id: Mapped[UUID] = mapped_column(ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False)
    order_item_id: Mapped[UUID] = mapped_column(ForeignKey("order_items.id", ondelete="CASCADE"), nullable=False)
    modifier_id: Mapped[UUID] = mapped_column(ForeignKey("menu_item_modifiers.id", ondelete="RESTRICT"), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class Payment(Base):
    __tablename__ = "payments"
    
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    restaurant_id: Mapped[UUID] = mapped_column(ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False)
    order_id: Mapped[UUID] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    payment_method: Mapped[PaymentMethod] = mapped_column(PG_ENUM(PaymentMethod, name="payment_method_enum"), nullable=False)
    status: Mapped[PaymentStatus] = mapped_column(
        PG_ENUM(PaymentStatus, name="payment_status_enum"), default=PaymentStatus.pending
    )
    transaction_id: Mapped[Optional[str]] = mapped_column(Text)
    mpesa_receipt_number: Mapped[Optional[str]] = mapped_column(Text)
    mpesa_result_code: Mapped[Optional[int]] = mapped_column(Integer)
    mpesa_result_description: Mapped[Optional[str]] = mapped_column(Text)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        CheckConstraint("amount > 0", name="payments_amount_check"),
    )

class WaiterCall(Base):
    __tablename__ = "waiter_calls"
    
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    restaurant_id: Mapped[UUID] = mapped_column(ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False)
    table_id: Mapped[UUID] = mapped_column(ForeignKey("tables.id", ondelete="CASCADE"), nullable=False)
    message: Mapped[Optional[str]] = mapped_column(Text)
    call_type: Mapped[CallType] = mapped_column(PG_ENUM(CallType, name="call_type_enum"), default=CallType.assistance)
    status: Mapped[CallStatus] = mapped_column(PG_ENUM(CallStatus, name="call_status_enum"), default=CallStatus.pending)
    acknowledged_by: Mapped[Optional[UUID]] = mapped_column(ForeignKey("staff.id", ondelete="SET NULL"))
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class OccasionMenu(Base):
    __tablename__ = "occasion_menus"
    
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    restaurant_id: Mapped[UUID] = mapped_column(ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        CheckConstraint("end_at > start_at", name="occasion_date_check"),
    )

class OccasionMenuItem(Base):
    __tablename__ = "occasion_menu_items"
    
    restaurant_id: Mapped[UUID] = mapped_column(ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False)
    occasion_menu_id: Mapped[UUID] = mapped_column(ForeignKey("occasion_menus.id", ondelete="CASCADE"), primary_key=True)
    menu_item_id: Mapped[UUID] = mapped_column(ForeignKey("menu_items.id", ondelete="CASCADE"), primary_key=True)
    special_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    
    __table_args__ = (
        CheckConstraint("special_price >= 0", name="occasion_price_check_v2"),
    )

class RestaurantSetting(Base):
    __tablename__ = "restaurant_settings"
    
    restaurant_id: Mapped[UUID] = mapped_column(ForeignKey("restaurants.id", ondelete="CASCADE"), primary_key=True)
    key: Mapped[str] = mapped_column(Text, primary_key=True)
    value: Mapped[dict] = mapped_column(JSONB, nullable=False)
    auto_clear_ready_minutes: Mapped[Optional[int]] = mapped_column(Integer, default=5, server_default="5")
    reservation_settings: Mapped[Optional[dict]] = mapped_column(JSONB, server_default='{"auto_release_minutes": 15, "require_deposit_for_party_size": 6, "deposit_amount": 1000, "max_reservation_days_ahead": 30, "min_cancel_hours": 2, "no_show_penalty": 500}')

class InventoryLog(Base):
    __tablename__ = "inventory_logs"
    
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    restaurant_id: Mapped[UUID] = mapped_column(ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False)
    menu_item_id: Mapped[UUID] = mapped_column(ForeignKey("menu_items.id", ondelete="CASCADE"), nullable=False)
    change_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(Text)
    staff_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("staff.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class ActivityLog(Base):
    __tablename__ = "activity_logs"
    
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    restaurant_id: Mapped[UUID] = mapped_column(ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False)
    staff_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("staff.id", ondelete="SET NULL"))
    action: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_info: Mapped[Optional[dict]] = mapped_column(JSONB, name="metadata")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class QRCodeScan(Base):
    __tablename__ = "qr_code_scans"
    
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    restaurant_id: Mapped[UUID] = mapped_column(ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False)
    table_id: Mapped[UUID] = mapped_column(ForeignKey("tables.id", ondelete="CASCADE"), nullable=False)
    session_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("customer_sessions.id", ondelete="SET NULL"))
    ip_address: Mapped[Optional[str]] = mapped_column(Text)
    user_agent: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

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

class StaffActivityLog(Base):
    __tablename__ = "staff_activity_logs"
    
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    staff_id: Mapped[UUID] = mapped_column(ForeignKey("staff.id", ondelete="CASCADE"), nullable=False)
    restaurant_id: Mapped[UUID] = mapped_column(ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False)
    clock_in_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    clock_out_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    shift_type_actual: Mapped[Optional[ShiftType]] = mapped_column(PG_ENUM(ShiftType, name="shift_type_enum"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class TableTransferLog(Base):
    __tablename__ = "table_transfer_logs"
    
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    restaurant_id: Mapped[UUID] = mapped_column(ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False)
    original_table_id: Mapped[UUID] = mapped_column(ForeignKey("tables.id", ondelete="CASCADE"), nullable=False)
    new_table_id: Mapped[UUID] = mapped_column(ForeignKey("tables.id", ondelete="CASCADE"), nullable=False)
    session_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("customer_sessions.id", ondelete="CASCADE"))
    transferred_by_staff_id: Mapped[UUID] = mapped_column(ForeignKey("staff.id", ondelete="CASCADE"), nullable=False)
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

class Reservations(Base):
    __tablename__ = "reservations"
    
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    restaurant_id: Mapped[UUID] = mapped_column(ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False)
    table_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("tables.id", ondelete="SET NULL"))
    
    guest_name: Mapped[str] = mapped_column(Text, nullable=False)
    guest_phone: Mapped[str] = mapped_column(Text, nullable=False)
    guest_email: Mapped[Optional[str]] = mapped_column(Text)
    party_size: Mapped[int] = mapped_column(Integer, nullable=False)
    
    reservation_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=90)
    status: Mapped[str] = mapped_column(Text, default="confirmed")
    
    special_requests: Mapped[Optional[str]] = mapped_column(Text)
    occasion: Mapped[Optional[str]] = mapped_column(Text)
    
    deposit_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), default=0)
    deposit_paid: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    deposit_payment_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("payments.id"))
    
    confirmed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    seated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    no_show_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    recurring_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True))
    recurring_frequency: Mapped[Optional[str]] = mapped_column(Text)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    restaurant: Mapped["Restaurant"] = relationship("Restaurant")
    table: Mapped[Optional["Table"]] = relationship("Table")

class Waitlist(Base):
    __tablename__ = "waitlist"
    
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    restaurant_id: Mapped[UUID] = mapped_column(ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False)
    
    guest_name: Mapped[str] = mapped_column(Text, nullable=False)
    guest_phone: Mapped[str] = mapped_column(Text, nullable=False)
    party_size: Mapped[int] = mapped_column(Integer, nullable=False)
    
    status: Mapped[str] = mapped_column(Text, default="waiting")
    position: Mapped[Optional[int]] = mapped_column(Integer)
    estimated_wait_minutes: Mapped[Optional[int]] = mapped_column(Integer)
    
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    seated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    notified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    sms_sent: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    sms_sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class ReservationTimeSlots(Base):
    __tablename__ = "reservation_time_slots"
    
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    restaurant_id: Mapped[UUID] = mapped_column(ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False)
    day_of_week: Mapped[Optional[int]] = mapped_column(Integer)
    start_time: Mapped[str] = mapped_column(Text, nullable=False)
    end_time: Mapped[str] = mapped_column(Text, nullable=False)
    interval_minutes: Mapped[Optional[int]] = mapped_column(Integer, default=30)
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
