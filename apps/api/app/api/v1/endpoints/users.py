"""User management API endpoints."""
import logging
from uuid import UUID
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from apps.api.app.core.database import get_db
from apps.api.app.core.permissions import require_permission, has_restaurant_access
from apps.api.app.core.auth import hash_password
from apps.api.app.models.user import User
from apps.api.app.models.role import Role
from apps.api.app.models.enums import UserStatus
from apps.api.app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    StaffInvite,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/", response_model=List[UserResponse])
async def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    user_status: Optional[UserStatus] = Query(None, alias="status"),
    role_id: Optional[UUID] = Query(None),
    current_user: User = Depends(require_permission("view_staff")),
    db: AsyncSession = Depends(get_db)
):
    """List all staff users in the current user's restaurant."""
    stmt = select(User).where(User.restaurant_id == current_user.restaurant_id)
    if user_status:
        stmt = stmt.where(User.status == user_status)
    if role_id:
        stmt = stmt.where(User.role_id == role_id)
    stmt = stmt.offset(skip).limit(limit)
    res = await db.execute(stmt)
    users = res.scalars().all()
    return [UserResponse.model_validate(u) for u in users]

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    current_user: User = Depends(require_permission("view_staff")),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific staff user by ID."""
    stmt = select(User).where(User.id == user_id)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    if not has_restaurant_access(current_user, user.restaurant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to user outside your restaurant"
        )
    return UserResponse.model_validate(user)

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(require_permission("add_staff")),
    db: AsyncSession = Depends(get_db)
):
    """Create a new staff user."""
    # Enforce restaurant boundary
    if user_data.restaurant_id != current_user.restaurant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot create user for another restaurant"
        )

    # Check email duplicate
    stmt = select(User).where(User.email == user_data.email.lower().strip())
    res = await db.execute(stmt)
    if res.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )

    # Check role existence
    role_stmt = select(Role).where(Role.id == user_data.role_id)
    role_res = await db.execute(role_stmt)
    role = role_res.scalar_one_or_none()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Specified role_id does not exist"
        )

    new_user = User(
        email=user_data.email.lower().strip(),
        phone=user_data.phone,
        password_hash=hash_password(user_data.password),
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        role_id=user_data.role_id,
        restaurant_id=user_data.restaurant_id,
        branch_id=user_data.branch_id,
        pin=user_data.pin,
        status=UserStatus.ACTIVE
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return UserResponse.model_validate(new_user)

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    user_data: UserUpdate,
    current_user: User = Depends(require_permission("edit_staff")),
    db: AsyncSession = Depends(get_db)
):
    """Update staff user details."""
    stmt = select(User).where(User.id == user_id)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    if not has_restaurant_access(current_user, user.restaurant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to user outside your restaurant"
        )

    if user_data.email:
        user.email = user_data.email.lower().strip()
    if user_data.phone is not None:
        user.phone = user_data.phone
    if user_data.first_name:
        user.first_name = user_data.first_name
    if user_data.last_name:
        user.last_name = user_data.last_name
    if user_data.role_id:
        role_stmt = select(Role).where(Role.id == user_data.role_id)
        role_res = await db.execute(role_stmt)
        if not role_res.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Role does not exist"
            )
        user.role_id = user_data.role_id
    if user_data.branch_id is not None:
        user.branch_id = user_data.branch_id
    if user_data.status:
        user.status = user_data.status

    await db.commit()
    await db.refresh(user)
    return UserResponse.model_validate(user)

@router.delete("/{user_id}")
async def delete_user(
    user_id: UUID,
    current_user: User = Depends(require_permission("delete_staff")),
    db: AsyncSession = Depends(get_db)
):
    """Soft delete (deactivate) a staff user."""
    stmt = select(User).where(User.id == user_id)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    if not has_restaurant_access(current_user, user.restaurant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to user outside your restaurant"
        )

    user.status = UserStatus.INACTIVE
    await db.commit()
    return {"message": f"User {user_id} successfully deactivated"}

@router.post("/{user_id}/pin")
async def set_pin(
    user_id: UUID,
    pin: str = Query(..., min_length=4, max_length=4, pattern=r"^[0-9]{4}$"),
    current_user: User = Depends(require_permission("edit_staff")),
    db: AsyncSession = Depends(get_db)
):
    """Set or update staff 4-digit PIN."""
    stmt = select(User).where(User.id == user_id)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    if not has_restaurant_access(current_user, user.restaurant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to user outside your restaurant"
        )

    user.pin = pin
    await db.commit()
    return {"message": "PIN updated successfully"}

@router.post("/{user_id}/activate")
async def activate_user(
    user_id: UUID,
    current_user: User = Depends(require_permission("edit_staff")),
    db: AsyncSession = Depends(get_db)
):
    """Activate staff user account."""
    stmt = select(User).where(User.id == user_id)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    if not has_restaurant_access(current_user, user.restaurant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    user.status = UserStatus.ACTIVE
    await db.commit()
    return {"message": "User activated successfully"}

@router.post("/{user_id}/deactivate")
async def deactivate_user(
    user_id: UUID,
    current_user: User = Depends(require_permission("edit_staff")),
    db: AsyncSession = Depends(get_db)
):
    """Deactivate staff user account."""
    stmt = select(User).where(User.id == user_id)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    if not has_restaurant_access(current_user, user.restaurant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    user.status = UserStatus.INACTIVE
    await db.commit()
    return {"message": "User deactivated successfully"}

@router.post("/invite", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def invite_staff(
    invite_data: StaffInvite,
    current_user: User = Depends(require_permission("add_staff")),
    db: AsyncSession = Depends(get_db)
):
    """Send staff invitation and create pending user account."""
    stmt = select(User).where(User.email == invite_data.email.lower().strip())
    res = await db.execute(stmt)
    if res.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )

    # Create pending user with dummy password (must be reset upon invite acceptance)
    dummy_pass = hash_password(f"InviteTempPassword_{invite_data.pin}_Secret")
    pending_user = User(
        email=invite_data.email.lower().strip(),
        phone=invite_data.phone,
        password_hash=dummy_pass,
        first_name=invite_data.first_name,
        last_name=invite_data.last_name,
        role_id=invite_data.role_id,
        restaurant_id=current_user.restaurant_id,
        branch_id=invite_data.branch_id,
        pin=invite_data.pin,
        status=UserStatus.PENDING
    )
    db.add(pending_user)
    await db.commit()
    await db.refresh(pending_user)
    logger.info(f"Staff invite sent to {pending_user.email} by {current_user.email}")
    return UserResponse.model_validate(pending_user)
