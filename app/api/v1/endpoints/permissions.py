"""Permission Management API Endpoints."""
from typing import List, Optional, Dict
from uuid import UUID
from collections import defaultdict
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.core.dependencies import require_permission
from app.services.permission_service import PermissionService
from app.schemas.permission import PermissionResponse, PermissionGroup
from app.schemas.role import RoleResponse
from app.models.permission import Permission

router = APIRouter(prefix="/permissions", tags=["permissions"])

@router.get("/", response_model=List[PermissionResponse])
async def list_permissions(
    category: Optional[str] = Query(None, description="Filter by category"),
    current_user = Depends(require_permission("manage_permissions")),
    db: AsyncSession = Depends(get_db)
):
    """List all permissions in the system, optionally filtered by category."""
    stmt = select(Permission)
    if category:
        stmt = stmt.where(Permission.category == category)
    result = await db.execute(stmt)
    return list(result.scalars().all())

@router.get("/groups", response_model=List[PermissionGroup])
async def get_permission_groups(
    current_user = Depends(require_permission("manage_permissions")),
    db: AsyncSession = Depends(get_db)
):
    """Get all permissions grouped by their category."""
    stmt = select(Permission)
    result = await db.execute(stmt)
    perms = list(result.scalars().all())

    grouped: Dict[str, List[PermissionResponse]] = defaultdict(list)
    for p in perms:
        grouped[p.category].append(PermissionResponse.model_validate(p))

    return [PermissionGroup(category=cat, permissions=p_list) for cat, p_list in grouped.items()]

@router.get("/{permission_id}", response_model=PermissionResponse)
async def get_permission(
    permission_id: UUID,
    current_user = Depends(require_permission("manage_permissions")),
    db: AsyncSession = Depends(get_db)
):
    """Get a permission by ID."""
    stmt = select(Permission).where(Permission.id == permission_id)
    result = await db.execute(stmt)
    perm = result.scalar_one_or_none()
    if not perm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Permission not found")
    return perm

@router.get("/user/{user_id}", response_model=List[str])
async def get_user_permissions(
    user_id: UUID,
    current_user = Depends(require_permission("view_staff")),
    db: AsyncSession = Depends(get_db)
):
    """Get all permission names granted to a specific user."""
    service = PermissionService(db)
    return await service.get_user_permissions(user_id=user_id)

@router.get("/user/{user_id}/roles", response_model=List[RoleResponse])
async def get_user_roles(
    user_id: UUID,
    current_user = Depends(require_permission("view_staff")),
    db: AsyncSession = Depends(get_db)
):
    """Get all roles assigned to a specific user."""
    service = PermissionService(db)
    return await service.get_user_roles(user_id=user_id)
