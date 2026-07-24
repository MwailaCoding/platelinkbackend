"""Pydantic schemas for roles."""
from uuid import UUID
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict

from apps.api.app.models.enums import RestaurantSize
from apps.api.app.schemas.permission import PermissionResponse

class RoleBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    level: int = Field(default=0, ge=0)
    restaurant_size: Optional[RestaurantSize] = None

class RoleCreate(RoleBase):
    restaurant_id: Optional[UUID] = None
    permission_ids: List[UUID] = Field(default_factory=list)

class RoleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    level: Optional[int] = Field(None, ge=0)
    restaurant_size: Optional[RestaurantSize] = None
    permission_ids: Optional[List[UUID]] = None

class RoleResponse(RoleBase):
    id: UUID
    is_system: bool
    is_custom: bool
    restaurant_id: Optional[UUID] = None
    permissions: List[PermissionResponse] = Field(default_factory=list)
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class RoleWithCounts(RoleResponse):
    user_count: int = 0
