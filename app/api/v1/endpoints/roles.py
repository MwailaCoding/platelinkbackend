"""Role management API endpoints."""
import logging
from uuid import UUID
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload

from apps.api.app.core.database import get_db
from apps.api.app.core.permissions import require_permission
from apps.api.app.models.role import Role
from apps.api.app.models.user import User
from apps.api.app.models.permission import Permission
from apps.api.app.models.enums import RestaurantSize
from apps.api.app.schemas.role import (
    RoleCreate,
    RoleUpdate,
    RoleResponse,
    RoleWithCounts,
)
from apps.api.app.schemas.permission import PermissionResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/roles", tags=["Roles"])

@router.get("/", response_model=List[RoleWithCounts])
async def get_roles(
    current_user: User = Depends(require_permission("view_staff")),
    db: AsyncSession = Depends(get_db)
):
    """List all roles applicable to the restaurant, including system roles and user counts."""
    # Select roles for user's restaurant OR system roles
    stmt = (
        select(Role)
        .options(selectinload(Role.permissions))
        .where(
            or_(
                Role.restaurant_id == current_user.restaurant_id,
                Role.restaurant_id.is_(None)
            )
        )
    )
    res = await db.execute(stmt)
    roles = res.scalars().all()

    # Get user counts per role for this restaurant
    count_stmt = (
        select(User.role_id, func.count(User.id))
        .where(User.restaurant_id == current_user.restaurant_id)
        .group_by(User.role_id)
    )
    count_res = await db.execute(count_stmt)
    counts = dict(count_res.all())

    result = []
    for r in roles:
        role_dict = RoleResponse.model_validate(r).model_dump()
        role_dict["user_count"] = counts.get(r.id, 0)
        result.append(RoleWithCounts(**role_dict))
    return result

@router.get("/default/{restaurant_size}", response_model=List[RoleResponse])
async def get_default_roles(
    restaurant_size: RestaurantSize,
    current_user: User = Depends(require_permission("manage_roles")),
    db: AsyncSession = Depends(get_db)
):
    """Get default system role templates for a specific restaurant size."""
    stmt = (
        select(Role)
        .options(selectinload(Role.permissions))
        .where(
            Role.restaurant_id.is_(None),
            Role.restaurant_size == restaurant_size
        )
    )
    res = await db.execute(stmt)
    roles = res.scalars().all()
    return [RoleResponse.model_validate(r) for r in roles]

@router.get("/{role_id}", response_model=RoleResponse)
async def get_role(
    role_id: UUID,
    current_user: User = Depends(require_permission("view_staff")),
    db: AsyncSession = Depends(get_db)
):
    """Get specific role details including permissions."""
    stmt = (
        select(Role)
        .options(selectinload(Role.permissions))
        .where(Role.id == role_id)
    )
    res = await db.execute(stmt)
    role = res.scalar_one_or_none()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    if role.restaurant_id is not None and role.restaurant_id != current_user.restaurant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to role from another restaurant"
        )
    return RoleResponse.model_validate(role)

@router.post("/", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(
    role_data: RoleCreate,
    current_user: User = Depends(require_permission("manage_roles")),
    db: AsyncSession = Depends(get_db)
):
    """Create a new custom role for the restaurant."""
    rest_id = current_user.restaurant_id

    # Check duplicate role name in restaurant
    stmt = select(Role).where(Role.restaurant_id == rest_id, Role.name == role_data.name.strip())
    res = await db.execute(stmt)
    if res.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Role with name '{role_data.name}' already exists in your restaurant"
        )

    # Fetch permissions to link
    permissions = []
    if role_data.permission_ids:
        perm_stmt = select(Permission).where(Permission.id.in_(role_data.permission_ids))
        perm_res = await db.execute(perm_stmt)
        permissions = perm_res.scalars().all()

    new_role = Role(
        name=role_data.name.strip(),
        description=role_data.description,
        level=role_data.level,
        is_system=False,
        is_custom=True,
        restaurant_id=rest_id,
        restaurant_size=role_data.restaurant_size,
        permissions=list(permissions)
    )
    db.add(new_role)
    await db.commit()
    await db.refresh(new_role)
    return RoleResponse.model_validate(new_role)

@router.put("/{role_id}", response_model=RoleResponse)
async def update_role(
    role_id: UUID,
    role_data: RoleUpdate,
    current_user: User = Depends(require_permission("manage_roles")),
    db: AsyncSession = Depends(get_db)
):
    """Update custom role details and assigned permissions."""
    stmt = (
        select(Role)
        .options(selectinload(Role.permissions))
        .where(Role.id == role_id)
    )
    res = await db.execute(stmt)
    role = res.scalar_one_or_none()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    if role.is_system:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot modify system roles"
        )
    if role.restaurant_id != current_user.restaurant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot modify role belonging to another restaurant"
        )

    if role_data.name is not None:
        role.name = role_data.name.strip()
    if role_data.description is not None:
        role.description = role_data.description
    if role_data.level is not None:
        role.level = role_data.level
    if role_data.restaurant_size is not None:
        role.restaurant_size = role_data.restaurant_size

    if role_data.permission_ids is not None:
        perm_stmt = select(Permission).where(Permission.id.in_(role_data.permission_ids))
        perm_res = await db.execute(perm_stmt)
        role.permissions = list(perm_res.scalars().all())

    await db.commit()
    await db.refresh(role)
    return RoleResponse.model_validate(role)

@router.delete("/{role_id}")
async def delete_role(
    role_id: UUID,
    current_user: User = Depends(require_permission("manage_roles")),
    db: AsyncSession = Depends(get_db)
):
    """Delete custom role if not system role and not currently assigned to users."""
    stmt = select(Role).where(Role.id == role_id)
    res = await db.execute(stmt)
    role = res.scalar_one_or_none()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    if role.is_system:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="System roles cannot be deleted"
        )
    if role.restaurant_id != current_user.restaurant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete role from another restaurant"
        )

    # Check if assigned to any active staff users
    user_count_stmt = select(func.count(User.id)).where(User.role_id == role_id)
    user_count_res = await db.execute(user_count_stmt)
    if user_count_res.scalar_one() > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete role while staff members are assigned to it"
        )

    await db.delete(role)
    await db.commit()
    return {"message": f"Role {role_id} successfully deleted"}

@router.get("/{role_id}/permissions", response_model=List[PermissionResponse])
async def get_role_permissions(
    role_id: UUID,
    current_user: User = Depends(require_permission("manage_permissions")),
    db: AsyncSession = Depends(get_db)
):
    """Get list of all permissions assigned to a role."""
    stmt = (
        select(Role)
        .options(selectinload(Role.permissions))
        .where(Role.id == role_id)
    )
    res = await db.execute(stmt)
    role = res.scalar_one_or_none()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    if role.restaurant_id is not None and role.restaurant_id != current_user.restaurant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    return [PermissionResponse.model_validate(p) for p in role.permissions]

@router.put("/{role_id}/permissions", response_model=List[PermissionResponse])
async def update_role_permissions(
    role_id: UUID,
    permission_ids: List[UUID],
    current_user: User = Depends(require_permission("manage_permissions")),
    db: AsyncSession = Depends(get_db)
):
    """Replace all assigned permissions for a role."""
    stmt = (
        select(Role)
        .options(selectinload(Role.permissions))
        .where(Role.id == role_id)
    )
    res = await db.execute(stmt)
    role = res.scalar_one_or_none()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    if role.is_system:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update system role permissions"
        )
    if role.restaurant_id != current_user.restaurant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    perm_stmt = select(Permission).where(Permission.id.in_(permission_ids))
    perm_res = await db.execute(perm_stmt)
    new_perms = perm_res.scalars().all()

    role.permissions = list(new_perms)
    await db.commit()
    await db.refresh(role)
    return [PermissionResponse.model_validate(p) for p in role.permissions]
