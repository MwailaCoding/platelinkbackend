"""Pydantic schemas for staff management."""
from uuid import UUID
from datetime import date, datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, EmailStr, Field, ConfigDict

class StaffStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ON_LEAVE = "on_leave"
    SUSPENDED = "suspended"
    TERMINATED = "terminated"

class StaffBase(BaseModel):
    employee_id: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    hire_date: Optional[date] = None
    salary: Optional[float] = None
    shift_preferences: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    skills: Optional[List[str]] = Field(default_factory=list)
    certifications: Optional[List[Dict[str, Any]]] = Field(default_factory=list)

class StaffCreate(StaffBase):
    email: EmailStr
    phone: Optional[str] = None
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    role_id: UUID
    branch_id: Optional[UUID] = None
    pin: str = Field(..., min_length=4, max_length=4)
    send_invite: bool = True

class StaffUpdate(BaseModel):
    employee_id: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    hire_date: Optional[date] = None
    status: Optional[StaffStatus] = None
    salary: Optional[float] = None
    shift_preferences: Optional[List[Dict[str, Any]]] = None
    skills: Optional[List[str]] = None
    certifications: Optional[List[Dict[str, Any]]] = None

class StaffResponse(StaffBase):
    id: UUID
    user_id: UUID
    status: StaffStatus = StaffStatus.ACTIVE
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class StaffWithUserResponse(StaffResponse):
    email: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    role: Optional[Dict[str, Any]] = None
    branch: Optional[Dict[str, Any]] = None
