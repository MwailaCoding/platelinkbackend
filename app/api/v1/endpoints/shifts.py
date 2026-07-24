"""Shifts and attendance API endpoints."""
import logging
from uuid import UUID
from datetime import date
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.core.database import get_db
from apps.api.app.core.permissions import require_permission
from apps.api.app.models.user import User
from apps.api.app.services.shift_service import ShiftService
from apps.api.app.schemas.shift import (
    StaffShiftCreate,
    StaffShiftUpdate,
    StaffShiftResponse,
    StaffCheckIn,
    StaffCheckOut,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/shifts", tags=["Shifts"])

@router.get("/", response_model=List[StaffShiftResponse])
async def list_shifts(
    start_date: date = Query(...),
    end_date: date = Query(...),
    staff_id: Optional[UUID] = Query(None),
    current_user: User = Depends(require_permission("view_staff")),
    db: AsyncSession = Depends(get_db)
):
    """List shifts in a date range."""
    service = ShiftService(db)
    shifts = await service.list_shifts(
        current_user.restaurant_id,
        start_date,
        end_date,
        staff_id
    )
    return [StaffShiftResponse.model_validate(s) for s in shifts]

@router.get("/{shift_id}", response_model=StaffShiftResponse)
async def get_shift(
    shift_id: UUID,
    current_user: User = Depends(require_permission("view_staff")),
    db: AsyncSession = Depends(get_db)
):
    """Get shift by ID."""
    service = ShiftService(db)
    shift = await service.get_shift(shift_id, current_user.restaurant_id)
    if not shift:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shift not found")
    return StaffShiftResponse.model_validate(shift)

@router.post("/", response_model=StaffShiftResponse, status_code=status.HTTP_201_CREATED)
async def create_shift(
    shift_data: StaffShiftCreate,
    current_user: User = Depends(require_permission("edit_staff")),
    db: AsyncSession = Depends(get_db)
):
    """Create new shift for a staff member."""
    service = ShiftService(db)
    data = shift_data.model_dump()
    data["created_by"] = current_user.id
    shift = await service.create_shift(
        shift_data.staff_id,
        current_user.restaurant_id,
        data
    )
    return StaffShiftResponse.model_validate(shift)

@router.put("/{shift_id}", response_model=StaffShiftResponse)
async def update_shift(
    shift_id: UUID,
    shift_data: StaffShiftUpdate,
    current_user: User = Depends(require_permission("edit_staff")),
    db: AsyncSession = Depends(get_db)
):
    """Update shift details."""
    service = ShiftService(db)
    shift = await service.update_shift(
        shift_id,
        current_user.restaurant_id,
        shift_data.model_dump(exclude_unset=True)
    )
    if not shift:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shift not found")
    return StaffShiftResponse.model_validate(shift)

@router.delete("/{shift_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_shift(
    shift_id: UUID,
    current_user: User = Depends(require_permission("edit_staff")),
    db: AsyncSession = Depends(get_db)
):
    """Delete shift."""
    service = ShiftService(db)
    success = await service.delete_shift(shift_id, current_user.restaurant_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shift not found")
    return None

@router.post("/check-in", response_model=Dict[str, Any])
async def check_in(
    data: StaffCheckIn,
    current_user: User = Depends(require_permission("view_staff")),
    db: AsyncSession = Depends(get_db)
):
    """Staff check-in for attendance."""
    service = ShiftService(db)
    attendance = await service.check_in(
        current_user.id,
        current_user.restaurant_id,
        method=data.method,
        latitude=data.latitude,
        longitude=data.longitude,
        shift_id=data.shift_id
    )
    return {
        "message": "Checked in successfully",
        "attendance_id": attendance.id,
        "check_in": attendance.check_in,
        "status": attendance.status
    }

@router.post("/check-out", response_model=Dict[str, Any])
async def check_out(
    data: StaffCheckOut,
    current_user: User = Depends(require_permission("view_staff")),
    db: AsyncSession = Depends(get_db)
):
    """Staff check-out from attendance."""
    service = ShiftService(db)
    attendance = await service.check_out(
        current_user.id,
        current_user.restaurant_id,
        method=data.method
    )
    return {
        "message": "Checked out successfully",
        "attendance_id": attendance.id,
        "check_out": attendance.check_out,
        "status": attendance.status
    }

@router.get("/summary/{summary_date}", response_model=Dict[str, Any])
async def get_shift_summary(
    summary_date: date,
    current_user: User = Depends(require_permission("view_staff")),
    db: AsyncSession = Depends(get_db)
):
    """Get daily shift summary."""
    service = ShiftService(db)
    return await service.get_shift_summary(current_user.restaurant_id, summary_date)
