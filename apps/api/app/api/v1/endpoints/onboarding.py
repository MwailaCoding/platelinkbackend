"""Onboarding, Branches, and Brand Customization API Endpoints."""
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, get_current_user
from app.core.dependencies import require_permission
from app.services.onboarding_service import OnboardingService
from app.schemas.branch import BranchCreate, BranchUpdate, BranchResponse
from app.schemas.onboarding import (
    OnboardingStatusResponse,
    BrandSettingsUpdate,
    BrandSettingsResponse,
    OnboardingCompleteResponse,
    RestaurantConfigResponse,
    RestaurantConfigUpdate,
)

router = APIRouter(prefix="/onboarding", tags=["onboarding"])

@router.get("/status", response_model=OnboardingStatusResponse)
async def get_onboarding_status(
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get onboarding status for current user's restaurant."""
    service = OnboardingService(db)
    return await service.get_or_create_onboarding_status(current_user.restaurant_id)

@router.put("/step/{step}", response_model=OnboardingStatusResponse)
async def update_onboarding_step(
    step: str,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Mark an onboarding step complete."""
    service = OnboardingService(db)
    return await service.update_onboarding_step(current_user.restaurant_id, step)

@router.post("/complete", response_model=OnboardingCompleteResponse)
async def complete_onboarding(
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Complete restaurant onboarding."""
    service = OnboardingService(db)
    return await service.complete_onboarding(current_user.restaurant_id)

# Brand Settings
@router.get("/brand/settings", response_model=BrandSettingsResponse)
async def get_brand_settings(
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get brand customization settings."""
    service = OnboardingService(db)
    return await service.get_or_create_brand_settings(current_user.restaurant_id)

@router.put("/brand/settings", response_model=BrandSettingsResponse)
async def update_brand_settings(
    data: BrandSettingsUpdate,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update brand customization settings."""
    service = OnboardingService(db)
    return await service.update_brand_settings(current_user.restaurant_id, data)

# Branches
@router.get("/branches", response_model=List[BranchResponse])
async def list_branches(
    current_user = Depends(require_permission("view_staff")),
    db: AsyncSession = Depends(get_db)
):
    """List all branches for the restaurant."""
    service = OnboardingService(db)
    return await service.list_branches(current_user.restaurant_id)

@router.post("/branches", response_model=BranchResponse, status_code=status.HTTP_201_CREATED)
async def create_branch(
    data: BranchCreate,
    current_user = Depends(require_permission("add_staff")),
    db: AsyncSession = Depends(get_db)
):
    """Create a new restaurant branch."""
    service = OnboardingService(db)
    return await service.create_branch(current_user.restaurant_id, data)

@router.put("/branches/{branch_id}", response_model=BranchResponse)
async def update_branch(
    branch_id: UUID,
    data: BranchUpdate,
    current_user = Depends(require_permission("edit_staff")),
    db: AsyncSession = Depends(get_db)
):
    """Update a restaurant branch."""
    service = OnboardingService(db)
    return await service.update_branch(branch_id, current_user.restaurant_id, data)

@router.delete("/branches/{branch_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_branch(
    branch_id: UUID,
    current_user = Depends(require_permission("delete_staff")),
    db: AsyncSession = Depends(get_db)
):
    """Delete a restaurant branch."""
    service = OnboardingService(db)
    await service.delete_branch(branch_id, current_user.restaurant_id)
