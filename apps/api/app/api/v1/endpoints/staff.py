# app/api/v1/endpoints/staff.py
from typing import List, Union
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core import security
from app.core.deps import get_db, get_current_user, check_role
from app.models import Staff, ActivityLog, StaffRole
from app.schemas import schemas

router = APIRouter()

@router.get("/", response_model=List[schemas.StaffRead])
async def list_staff(
    current_user: Staff = Depends(check_role(["owner", "manager"])),
    db: AsyncSession = Depends(get_db)
):
    """
    List all staff for the restaurant.
    """
    stmt = select(Staff).where(Staff.restaurant_id == current_user.restaurant_id)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/", response_model=schemas.StaffRead)
async def create_staff(
    data: schemas.StaffCreate,
    current_user: Staff = Depends(check_role(["owner", "manager", "branch_manager"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new staff member.
    """
    if current_user.role.value == 'owner' or getattr(current_user, 'role_type', '') == 'owner':
        branch_id = getattr(data, 'branch_id', None)
    elif getattr(current_user, 'role_type', '') == 'branch_manager' or current_user.role.value == 'branch_manager':
        req_branch_id = str(getattr(data, 'branch_id', ''))
        if req_branch_id and req_branch_id != str(current_user.branch_id):
            raise HTTPException(403, "Cannot assign staff to other branches")
        branch_id = current_user.branch_id
    else:
        raise HTTPException(403, "Only owner or branch manager can add staff")

    # Check if PIN is unique in restaurant
    stmt = select(Staff).where(Staff.restaurant_id == current_user.restaurant_id)
    result = await db.execute(stmt)
    existing_staff = result.scalars().all()
    for s in existing_staff:
        if security.verify_pin(data.pin_code, s.pin_code):
            raise HTTPException(status_code=400, detail="PIN code already in use by another staff member")
            
    new_staff = Staff(
        restaurant_id=current_user.restaurant_id,
        branch_id=branch_id,
        full_name=data.full_name,
        role=data.role,
        role_type=getattr(data, 'role_type', 'waiter'),
        shift=data.shift,
        pin_code=security.get_password_hash(data.pin_code),
        assigned_tables=data.assigned_tables,
        kitchen_station=data.kitchen_station
    )
    db.add(new_staff)
    await db.commit()
    await db.refresh(new_staff)
    return new_staff

@router.post("/bulk")
async def bulk_create_staff(
    data: Union[List[schemas.StaffCreate], schemas.BulkStaffInput],
    current_user: Staff = Depends(check_role(["owner"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Bulk create staff members in a transaction.
    """
    staff_items = data if isinstance(data, list) else data.staff
    pins = [s.pin_code for s in staff_items]
    if len(pins) != len(set(pins)):
        raise HTTPException(status_code=400, detail="Duplicate PINs in request")
        
    for s_data in staff_items:
        new_staff = Staff(
            restaurant_id=current_user.restaurant_id,
            full_name=s_data.full_name,
            role=s_data.role,
            shift=s_data.shift,
            pin_code=security.get_password_hash(s_data.pin_code),
            assigned_tables=s_data.assigned_tables,
            kitchen_station=s_data.kitchen_station
        )
        db.add(new_staff)
        
    await db.commit()
    return {"msg": f"Successfully created {len(staff_items)} staff members"}

@router.get("/me", response_model=schemas.StaffRead)
async def get_staff_me(
    current_user: Staff = Depends(get_current_user)
):
    """
    Get current logged in staff profile.
    """
    return current_user

@router.get("/{staff_id}", response_model=schemas.StaffRead)
async def get_staff_detail(
    staff_id: str,
    current_user: Staff = Depends(check_role(["owner", "manager"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Get staff member details.
    """
    stmt = select(Staff).where(
        Staff.id == staff_id,
        Staff.restaurant_id == current_user.restaurant_id
    )
    result = await db.execute(stmt)
    staff = result.scalar_one_or_none()
    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")
    return staff

@router.put("/{staff_id}", response_model=schemas.StaffRead)
async def update_staff(
    staff_id: str,
    data: schemas.StaffUpdate,
    current_user: Staff = Depends(check_role(["owner", "manager"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Update staff member.
    """
    stmt = select(Staff).where(
        Staff.id == staff_id,
        Staff.restaurant_id == current_user.restaurant_id
    )
    result = await db.execute(stmt)
    staff = result.scalar_one_or_none()
    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")
        
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(staff, field, value)
        
    await db.commit()
    await db.refresh(staff)
    return staff

@router.delete("/{staff_id}")
async def delete_staff(
    staff_id: str,
    current_user: Staff = Depends(check_role(["owner"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Soft delete a staff member.
    """
    stmt = select(Staff).where(
        Staff.id == staff_id,
        Staff.restaurant_id == current_user.restaurant_id
    )
    result = await db.execute(stmt)
    staff = result.scalar_one_or_none()
    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")
        
    staff.is_active = False
    db.add(ActivityLog(
        restaurant_id=current_user.restaurant_id,
        staff_id=current_user.id,
        action=f"deleted_staff_{staff_id}"
    ))
    await db.commit()
    return {"msg": "Staff deactivated"}

@router.put("/{staff_id}/reset-pin")
async def reset_pin(
    staff_id: str,
    new_pin: str = Body(..., embed=True),
    current_user: Staff = Depends(check_role(["owner", "manager"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Reset staff PIN code.
    """
    if not new_pin.isdigit() or len(new_pin) < 4:
        raise HTTPException(status_code=400, detail="Invalid PIN format")
        
    stmt = select(Staff).where(
        Staff.id == staff_id,
        Staff.restaurant_id == current_user.restaurant_id
    )
    result = await db.execute(stmt)
    staff = result.scalar_one_or_none()
    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")
        
    staff.pin_code = security.get_password_hash(new_pin)
    await db.commit()
    return {"msg": "PIN reset successful"}

