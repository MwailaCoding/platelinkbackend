"""Permission Pydantic Schemas."""
from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict

class PermissionBase(BaseModel):
    name: str
    resource: str
    action: str
    description: Optional[str] = None
    category: str

class PermissionCreate(PermissionBase):
    pass

class PermissionResponse(PermissionBase):
    id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class PermissionGroup(BaseModel):
    category: str
    permissions: List[PermissionResponse]

    model_config = ConfigDict(from_attributes=True)
