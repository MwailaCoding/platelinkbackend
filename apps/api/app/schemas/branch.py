"""Branch & Multi-Branch Pydantic schemas."""
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, EmailStr

class BranchBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    address: Optional[str] = None
    city: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    is_active: bool = True

class BranchCreate(BranchBase):
    manager_id: Optional[UUID] = None

class BranchUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
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
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class BranchSwitchRequest(BaseModel):
    branch_id: UUID

class RestaurantConfigUpdate(BaseModel):
    size: Optional[str] = None
    type: Optional[str] = None
    is_multi_branch: Optional[bool] = None
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
