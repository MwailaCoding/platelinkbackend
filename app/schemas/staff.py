# app/schemas/base.py
from pydantic import BaseModel, ConfigDict

class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

# app/schemas/restaurant.py
from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import EmailStr, field_validator
from app.schemas.base import BaseSchema

class RestaurantBase(BaseSchema):
    name: str
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None

class RestaurantCreate(RestaurantBase):
    subdomain: str
    owner_name: str
    password: str

class RestaurantUpdate(BaseSchema):
    name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    logo_url: Optional[str] = None

class RestaurantRead(RestaurantBase):
    id: UUID
    slug: str
    subdomain: str
    is_onboarded: bool
    created_at: datetime

# app/schemas/staff.py
from typing import Optional, List
from uuid import UUID
from app.schemas.base import BaseSchema
from app.models.enums import StaffRole, ShiftType

class StaffBase(BaseSchema):
    full_name: str
    role: StaffRole
    shift: ShiftType = ShiftType.full
    assigned_tables: Optional[List[int]] = None

class StaffCreate(StaffBase):
    pin_code: str
    
    @field_validator('pin_code')
    def validate_pin(cls, v):
        if not v.isdigit() or not (4 <= len(v) <= 6):
            raise ValueError('PIN must be 4-6 digits')
        return v

class StaffUpdate(BaseSchema):
    full_name: Optional[str] = None
    role: Optional[StaffRole] = None
    shift: Optional[ShiftType] = None
    assigned_tables: Optional[List[int]] = None
    is_active: Optional[bool] = None

class StaffRead(StaffBase):
    id: UUID
    restaurant_id: UUID
    is_active: bool
