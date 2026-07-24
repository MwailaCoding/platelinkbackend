"""Pydantic schemas for permissions."""
from uuid import UUID
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict

from apps.api.app.models.enums import PermissionAction, PermissionCategory

class PermissionBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    resource: str = Field(..., min_length=1, max_length=50)
    action: PermissionAction
    description: Optional[str] = None
    category: PermissionCategory

class PermissionCreate(PermissionBase):
    pass

class PermissionResponse(PermissionBase):
    id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class PermissionGroup(BaseModel):
    category: PermissionCategory
    permissions: List[PermissionResponse]
