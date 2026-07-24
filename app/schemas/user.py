"""Pydantic schemas for users and authentication."""
from uuid import UUID
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict

from apps.api.app.models.enums import UserStatus
from apps.api.app.schemas.role import RoleResponse

class UserBase(BaseModel):
    email: EmailStr
    phone: Optional[str] = None
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    role_id: UUID
    branch_id: Optional[UUID] = None

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    restaurant_id: UUID
    pin: Optional[str] = Field(None, min_length=4, max_length=4)

class UserRegisterRequest(BaseModel):
    restaurant_name: str = Field(..., min_length=1, max_length=200)
    subdomain: str = Field(..., min_length=1, max_length=100)
    owner_name: Optional[str] = "Admin"
    email: EmailStr
    password: str = Field(..., min_length=8)
    phone: Optional[str] = None
    restaurant_size: Optional[str] = "medium"
    restaurant_type: Optional[str] = "single"

# Alias for backwards compatibility with live Render API schema
UserRegister = UserRegisterRequest

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    role_id: Optional[UUID] = None
    branch_id: Optional[UUID] = None
    status: Optional[UserStatus] = None

class UserResponse(UserBase):
    id: UUID
    status: UserStatus
    last_login: Optional[datetime] = None
    created_at: datetime
    restaurant_id: UUID
    role: Optional[RoleResponse] = None

    model_config = ConfigDict(from_attributes=True)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserPINLogin(BaseModel):
    email: EmailStr
    pin: str = Field(..., min_length=4, max_length=4)

class UserQRLogin(BaseModel):
    user_id: UUID
    qr_code: str

class StaffInvite(BaseModel):
    email: EmailStr
    phone: Optional[str] = None
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    role_id: UUID
    branch_id: Optional[UUID] = None
    pin: str = Field(..., min_length=4, max_length=4)
    message: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse
