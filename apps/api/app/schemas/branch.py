"""Branch Pydantic Schemas."""
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, EmailStr

class BranchBase(BaseModel):
    name: str
    address: Optional[str] = None
    city: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None

class BranchCreate(BranchBase):
    restaurant_id: Optional[UUID] = None

class BranchUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    manager_id: Optional[UUID] = None
    is_active: Optional[bool] = None

class BranchResponse(BranchBase):
    id: UUID
    restaurant_id: UUID
    manager_id: Optional[UUID] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
