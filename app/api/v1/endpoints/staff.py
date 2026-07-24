"""Staff management API endpoints."""
import logging
from uuid import UUID
from datetime import date
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.core.database import get_db
from apps.api.app.core.permissions import require_permission
from apps.api.app.models.user import User
from apps.api.app.services.staff_service import StaffService
from apps.api.app.schemas.staff import (
    StaffCreate,
    StaffUpdate,
    StaffResponse,
    StaffWithUserResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/staff", tags=["Staff"])

@router.get("/", response_model=List[StaffWithUserResponse])
async def list_staff(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    user_status: Optional[str] = Query(None, alias="status"),
    role_id: Optional[UUID] = Query(None),
    department: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    current_user: User = Depends(require_permission("view_staff")),
    db: AsyncSession = Depends(get_db)
):
    """List staff members with filters and pagination."""
    service = StaffService(db)
    staff_list, total = await service.list_staff(
        current_user.restaurant_id,
        skip, limit, user_status, role_id, department, search
    )
    return [StaffWithUserResponse(**item) for item in staff_list]

@router.get("/online", response_model=List[Dict[str, Any]])
async def get_online_staff(
    current_user: User = Depends(require_permission("view_staff")),
    db: AsyncSession = Depends(get_db)
):
    """Get currently online/checked-in staff members."""
    service = StaffService(db)
    return await service.get_online_staff(current_user.restaurant_id)

@router.get("/{staff_id}", response_model=StaffWithUserResponse)
async def get_staff(
    staff_id: UUID,
    current_user: User = Depends(require_permission("view_staff")),
    db: AsyncSession = Depends(get_db)
):
    """Get staff member by ID."""
    service = StaffService(db)
    staff = await service.get_staff(staff_id, current_user.restaurant_id)
    if not staff:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff not found")

    u = staff.user
    item = {
        "id": staff.id,
        "user_id": staff.user_id,
        "employee_id": staff.employee_id,
        "department": staff.department,
        "position": staff.position,
        "hire_date": staff.hire_date,
        "salary": staff.salary,
        "shift_preferences": staff.shift_preferences or [],
        "skills": staff.skills or [],
        "certifications": staff.certifications or [],
        "status": u.status if u else "active",
        "created_at": staff.created_at,
        "email": u.email if u else "",
        "first_name": u.first_name if u else "",
        "last_name": u.last_name if u else "",
        "phone": u.phone if u else None,
        "role": {"id": u.role.id, "name": u.role.name} if u and u.role else None,
        "branch": None
    }
    return StaffWithUserResponse(**item)

@router.post("/", response_model=StaffResponse, status_code=status.HTTP_201_CREATED)
async def create_staff(
    staff_data: StaffCreate,
    current_user: User = Depends(require_permission("add_staff")),
    db: AsyncSession = Depends(get_db)
):
    """Create new staff member and user profile."""
    service = StaffService(db)
    u_dict = staff_data.model_dump()
    s_dict = {
        "employee_id": staff_data.employee_id,
        "department": staff_data.department,
        "position": staff_data.position,
        "hire_date": staff_data.hire_date,
        "salary": staff_data.salary,
        "shift_preferences": staff_data.shift_preferences,
        "skills": staff_data.skills,
        "certifications": staff_data.certifications,
    }
    staff = await service.create_staff(current_user.restaurant_id, u_dict, s_dict)
    return StaffResponse.model_validate(staff)

@router.put("/{staff_id}", response_model=StaffResponse)
async def update_staff(
    staff_id: UUID,
    staff_data: StaffUpdate,
    current_user: User = Depends(require_permission("edit_staff")),
    db: AsyncSession = Depends(get_db)
):
    """Update staff member details."""
    service = StaffService(db)
    staff = await service.update_staff(
        staff_id,
        current_user.restaurant_id,
        staff_data.model_dump(exclude_unset=True)
    )
    if not staff:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff not found")
    return StaffResponse.model_validate(staff)

@router.delete("/{staff_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_staff(
    staff_id: UUID,
    current_user: User = Depends(require_permission("delete_staff")),
    db: AsyncSession = Depends(get_db)
):
    """Soft delete staff member."""
    service = StaffService(db)
    success = await service.delete_staff(staff_id, current_user.restaurant_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff not found")
    return None

@router.get("/{staff_id}/performance", response_model=Dict[str, Any])
async def get_staff_performance(
    staff_id: UUID,
    period_start: Optional[date] = Query(None),
    period_end: Optional[date] = Query(None),
    current_user: User = Depends(require_permission("view_staff")),
    db: AsyncSession = Depends(get_db)
):
    """Get staff performance metrics."""
    service = StaffService(db)
    return await service.get_staff_performance(
        staff_id,
        current_user.restaurant_id,
        period_start,
        period_end
    )
