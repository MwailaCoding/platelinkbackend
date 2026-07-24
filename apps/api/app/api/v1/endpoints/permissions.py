"""Permission API endpoints."""
import logging
from uuid import UUID
from typing import List, Optional, Dict

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from apps.api.app.core.database import get_db
from apps.api.app.core.permissions import require_permission
from apps.api.app.models.permission import Permission
from apps.api.app.models.user import User
from apps.api.app.models.enums import PermissionCategory
from apps.api.app.schemas.permission import PermissionResponse, PermissionGroup

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/permissions", tags=["Permissions"])

@router.get("/", response_model=List[PermissionResponse])
async def get_permissions(
    category: Optional[PermissionCategory] = Query(None),
    current_user: User = Depends(require_permission("view_staff")),
    db: AsyncSession = Depends(get_db)
):
    """List system permissions with optional category filter."""
    stmt = select(Permission)
    if category:
        stmt = stmt.where(Permission.category == category)
    res = await db.execute(stmt)
    perms = res.scalars().all()
    return [PermissionResponse.model_validate(p) for p in perms]

@router.get("/groups", response_model=List[PermissionGroup])
async def get_permission_groups(
    current_user: User = Depends(require_permission("view_staff")),
    db: AsyncSession = Depends(get_db)
):
    """Get system permissions grouped by category."""
    stmt = select(Permission)
    res = await db.execute(stmt)
    perms = res.scalars().all()

    grouped: Dict[PermissionCategory, List[PermissionResponse]] = {}
    for p in perms:
        if p.category not in grouped:
            grouped[p.category] = []
        grouped[p.category].append(PermissionResponse.model_validate(p))

    return [
        PermissionGroup(category=cat, permissions=p_list)
        for cat, p_list in grouped.items()
    ]

@router.get("/{permission_id}", response_model=PermissionResponse)
async def get_permission(
    permission_id: UUID,
    current_user: User = Depends(require_permission("view_staff")),
    db: AsyncSession = Depends(get_db)
):
    """Get specific permission details by ID."""
    stmt = select(Permission).where(Permission.id == permission_id)
    res = await db.execute(stmt)
    perm = res.scalar_one_or_none()
    if not perm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not found"
        )
    return PermissionResponse.model_validate(perm)
