"""Pydantic schemas for shifts and attendance."""
from uuid import UUID
from datetime import date, time, datetime
from typing import Optional
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict

class ShiftStatus(str, Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"

class AttendanceStatus(str, Enum):
    PRESENT = "present"
    ABSENT = "absent"
    LATE = "late"
    EARLY_LEAVE = "early_leave"

class StaffShiftBase(BaseModel):
    shift_date: date
    start_time: time
    end_time: time
    break_start: Optional[time] = None
    break_end: Optional[time] = None
    notes: Optional[str] = None

class StaffShiftCreate(StaffShiftBase):
    staff_id: UUID

class StaffShiftUpdate(BaseModel):
    shift_date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    break_start: Optional[time] = None
    break_end: Optional[time] = None
    status: Optional[ShiftStatus] = None
    notes: Optional[str] = None

class StaffShiftResponse(StaffShiftBase):
    id: UUID
    staff_id: UUID
    status: ShiftStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class StaffCheckIn(BaseModel):
    method: str = Field(..., pattern=r"^(qr|pin|manual)$")
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    shift_id: Optional[UUID] = None

class StaffCheckOut(BaseModel):
    method: str = Field(..., pattern=r"^(qr|pin|manual)$")
