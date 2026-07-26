"""Pydantic schemas for Cashier PIN authentication and session management."""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime

class PinLoginRequest(BaseModel):
    user_id: Optional[Any] = None
    pin: str = Field(..., min_length=4, max_length=4, pattern="^[0-9]{4}$")
    terminal_id: Optional[str] = "Terminal-1"

class PinSetupRequest(BaseModel):
    user_id: UUID
    pin: str = Field(..., min_length=4, max_length=4, pattern="^[0-9]{4}$")
    confirm_pin: str = Field(..., min_length=4, max_length=4, pattern="^[0-9]{4}$")

class PinChangeRequest(BaseModel):
    user_id: UUID
    current_pin: str = Field(..., min_length=4, max_length=4, pattern="^[0-9]{4}$")
    new_pin: str = Field(..., min_length=4, max_length=4, pattern="^[0-9]{4}$")
    confirm_pin: str = Field(..., min_length=4, max_length=4, pattern="^[0-9]{4}$")

class PinResetRequest(BaseModel):
    user_id: UUID
    new_pin: str = Field(..., min_length=4, max_length=4, pattern="^[0-9]{4}$")

class PinVerifyRequest(BaseModel):
    user_id: UUID
    pin: str = Field(..., min_length=4, max_length=4, pattern="^[0-9]{4}$")
    reason: Optional[str] = None  # e.g., "refund", "void"

class PinLoginResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    session_id: UUID
    user: Dict[str, Any]
    requires_pin_setup: bool = False

class SessionResponse(BaseModel):
    id: UUID
    user_id: UUID
    terminal_id: Optional[str] = None
    logged_in_at: datetime
    last_activity_at: datetime
    logged_out_at: Optional[datetime] = None
    status: str = "active"
    is_active: bool = True

class LogoutRequest(BaseModel):
    session_id: UUID

class ExtendSessionRequest(BaseModel):
    session_id: UUID

class LockSessionRequest(BaseModel):
    session_id: UUID

class UnlockSessionRequest(BaseModel):
    session_id: UUID
    pin: str = Field(..., min_length=4, max_length=4, pattern="^[0-9]{4}$")
