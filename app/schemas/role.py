"""Role Pydantic Schemas."""
from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict
from app.schemas.permission import PermissionResponse

class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None
    level: int = 0
    restaurant_id: Optional[UUID] = None

class RoleCreate(RoleBase):
    permission_ids: List[UUID] = []

class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    level: Optional[int] = None
    permission_ids: Optional[List[UUID]] = None

class RoleResponse(RoleBase):
    id: UUID
    is_system: bool = False
    is_custom: bool = False
    permissions: List[PermissionResponse] = []
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class RoleWithCount(RoleResponse):
    user_count: int = 0

    model_config = ConfigDict(from_attributes=True)
