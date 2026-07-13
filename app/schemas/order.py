# app/schemas/menu.py
from typing import Optional, List
from decimal import Decimal
from uuid import UUID
from app.schemas.base import BaseSchema

class CategoryBase(BaseSchema):
    name: str
    display_order: int = 0

class CategoryCreate(CategoryBase):
    pass

class CategoryRead(CategoryBase):
    id: UUID
    is_active: bool

class MenuItemBase(BaseSchema):
    name: str
    description: Optional[str] = None
    price: Decimal
    category_id: UUID
    is_available: bool = True
    stock_quantity: Optional[int] = None

class MenuItemCreate(MenuItemBase):
    pass

class MenuItemRead(MenuItemBase):
    id: UUID
    low_stock_threshold: int

# app/schemas/order.py
from typing import List, Optional
from decimal import Decimal
from uuid import UUID
from datetime import datetime
from app.schemas.base import BaseSchema
from app.models.enums import OrderStatus, PaymentStatus, PaymentMethod

class OrderItemBase(BaseSchema):
    menu_item_id: UUID
    quantity: int
    special_instructions: Optional[str] = None

class OrderItemRead(OrderItemBase):
    id: UUID
    unit_price: Decimal
    subtotal: Decimal
    status: OrderStatus

class OrderRead(BaseSchema):
    id: UUID
    order_number: str
    status: OrderStatus
    subtotal: Decimal
    tax: Decimal
    total: Decimal
    payment_status: PaymentStatus
    payment_method: Optional[PaymentMethod] = None
    created_at: datetime
    items: List[OrderItemRead] = []
