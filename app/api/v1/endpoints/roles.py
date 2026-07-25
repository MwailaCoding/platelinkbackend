"""Role Management API Endpoints."""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, get_current_user
from app.core.dependencies import require_permission
from app.services.role_service import RoleService
from app.schemas.role import RoleCreate, RoleUpdate, RoleResponse
from app.schemas.permission import PermissionResponse

router = APIRouter(prefix="/roles", tags=["roles"])

@router.get("/", response_model=List[RoleResponse])
async def list_roles(
    include_system: bool = Query(True, description="Include system roles"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    current_user = Depends(require_permission("view_staff")),
    db: AsyncSession = Depends(get_db)
):
    """List all roles available for the current user's restaurant."""
    service = RoleService(db)
    restaurant_id = getattr(current_user, "restaurant_id", None)
    return await service.list_roles(restaurant_id=restaurant_id, include_system=include_system, skip=skip, limit=limit)

@router.get("/system", response_model=List[RoleResponse])
async def get_system_roles(
    current_user = Depends(require_permission("view_staff")),
    db: AsyncSession = Depends(get_db)
):
    """Get all global system template roles."""
    service = RoleService(db)
    return await service.get_system_roles()

@router.get("/{role_id}", response_model=RoleResponse)
async def get_role(
    role_id: UUID,
    current_user = Depends(require_permission("view_staff")),
    db: AsyncSession = Depends(get_db)
):
    """Get role details by ID."""
    service = RoleService(db)
    restaurant_id = getattr(current_user, "restaurant_id", None)
    role = await service.get_role(role_id=role_id, restaurant_id=restaurant_id)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    return role

@router.post("/", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(
    role_data: RoleCreate,
    current_user = Depends(require_permission("manage_roles")),
    db: AsyncSession = Depends(get_db)
):
    """Create a new custom role for the restaurant."""
    service = RoleService(db)
    restaurant_id = getattr(current_user, "restaurant_id", None) or role_data.restaurant_id
    if not restaurant_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Restaurant ID is required")

    return await service.create_role(
        name=role_data.name,
        restaurant_id=restaurant_id,
        permission_ids=role_data.permission_ids,
        description=role_data.description,
        level=role_data.level
    )

@router.put("/{role_id}", response_model=RoleResponse)
async def update_role(
    role_id: UUID,
    role_data: RoleUpdate,
    current_user = Depends(require_permission("manage_roles")),
    db: AsyncSession = Depends(get_db)
):
    """Update a custom role and its assigned permissions."""
    service = RoleService(db)
    restaurant_id = getattr(current_user, "restaurant_id", None)
    return await service.update_role(
        role_id=role_id,
        restaurant_id=restaurant_id,
        name=role_data.name,
        description=role_data.description,
        level=role_data.level,
        permission_ids=role_data.permission_ids
    )

@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(
    role_id: UUID,
    current_user = Depends(require_permission("manage_roles")),
    db: AsyncSession = Depends(get_db)
):
    """Delete a custom role."""
    service = RoleService(db)
    restaurant_id = getattr(current_user, "restaurant_id", None)
    await service.delete_role(role_id=role_id, restaurant_id=restaurant_id)

@router.get("/{role_id}/permissions", response_model=List[PermissionResponse])
async def get_role_permissions(
    role_id: UUID,
    current_user = Depends(require_permission("manage_permissions")),
    db: AsyncSession = Depends(get_db)
):
    """Get all permissions assigned to a specific role."""
    service = RoleService(db)
    return await service.get_role_permissions(role_id=role_id)

@router.put("/{role_id}/permissions", response_model=List[PermissionResponse])
async def update_role_permissions(
    role_id: UUID,
    permission_ids: List[UUID],
    current_user = Depends(require_permission("manage_permissions")),
    db: AsyncSession = Depends(get_db)
):
    """Replace assigned permissions for a custom role."""
    service = RoleService(db)
    restaurant_id = getattr(current_user, "restaurant_id", None)
    await service.update_role(role_id=role_id, restaurant_id=restaurant_id, permission_ids=permission_ids)
    return await service.get_role_permissions(role_id=role_id)
