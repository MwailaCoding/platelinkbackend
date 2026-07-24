"""Pydantic schemas for staff invitations."""
from uuid import UUID
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict

class StaffInviteBase(BaseModel):
    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    role_id: UUID
    branch_id: Optional[UUID] = None
    phone: Optional[str] = None
    message: Optional[str] = None

class StaffInviteCreate(StaffInviteBase):
    pin: str = Field(..., min_length=4, max_length=4)

class StaffInviteResponse(BaseModel):
    id: UUID
    email: str
    status: str
    expires_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class AcceptInvitationRequest(BaseModel):
    password: str = Field(..., min_length=8)
    phone: Optional[str] = None
