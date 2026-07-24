"""Branch management API endpoints."""
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.core.database import get_db
from apps.api.app.core.auth import get_current_user
from apps.api.app.core.permissions import require_permission
from apps.api.app.models.user import User
from apps.api.app.schemas.branch import (
    BranchCreate,
    BranchUpdate,
    BranchResponse,
    BranchSwitchRequest,
)
from apps.api.app.services.branch_service import BranchService

router = APIRouter()

@router.get("/", response_model=List[BranchResponse])
async def list_branches(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("view_settings"))
):
    """List all branch locations for the current restaurant."""
    return await BranchService.list_branches(db, current_user.restaurant_id)

@router.post("/", response_model=BranchResponse, status_code=status.HTTP_201_CREATED)
async def create_branch(
    data: BranchCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("manage_settings"))
):
    """Create a new branch location."""
    return await BranchService.create_branch(db, current_user.restaurant_id, data)

@router.get("/{branch_id}", response_model=BranchResponse)
async def get_branch(
    branch_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("view_settings"))
):
    """Get details of a specific branch."""
    return await BranchService.get_branch(db, branch_id, current_user.restaurant_id)

@router.put("/{branch_id}", response_model=BranchResponse)
async def update_branch(
    branch_id: UUID,
    data: BranchUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("manage_settings"))
):
    """Update branch configuration."""
    return await BranchService.update_branch(db, branch_id, current_user.restaurant_id, data)

@router.delete("/{branch_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_branch(
    branch_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("manage_settings"))
):
    """Deactivate a branch location."""
    await BranchService.delete_branch(db, branch_id, current_user.restaurant_id)

@router.post("/switch")
async def switch_branch(
    data: BranchSwitchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Switch active branch for current user session."""
    user = await BranchService.switch_user_branch(
        db, current_user.id, current_user.restaurant_id, data.branch_id
    )
    return {"message": "Active branch updated successfully", "branch_id": user.branch_id}
