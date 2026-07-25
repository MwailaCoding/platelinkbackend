"""Service layer for Onboarding, Branches, and Brand Customization."""
import logging
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.restaurant import Restaurant
from app.models.branch import Branch
from app.models.onboarding import OnboardingStatus
from app.models.brand_settings import BrandSettings
from app.models.staff import Staff
from app.schemas.branch import BranchCreate, BranchUpdate, BranchResponse
from app.schemas.onboarding import (
    BrandSettingsCreate,
    BrandSettingsUpdate,
    RestaurantConfigUpdate,
    OnboardingCompleteResponse,
)

logger = logging.getLogger(__name__)

class OnboardingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_onboarding_status(self, restaurant_id: UUID) -> OnboardingStatus:
        """Get or initialize onboarding status for a restaurant."""
        stmt = select(OnboardingStatus).where(OnboardingStatus.restaurant_id == restaurant_id)
        res = await self.db.execute(stmt)
        status_obj = res.scalar_one_or_none()
        if not status_obj:
            status_obj = OnboardingStatus(
                restaurant_id=restaurant_id,
                step_completed=["account_creation"],
                is_complete=False
            )
            self.db.add(status_obj)
            await self.db.flush()
        return status_obj

    async def update_onboarding_step(self, restaurant_id: UUID, step: str) -> OnboardingStatus:
        """Mark an onboarding step as completed."""
        status_obj = await self.get_or_create_onboarding_status(restaurant_id)
        current_steps = list(status_obj.step_completed or [])
        if step not in current_steps:
            current_steps.append(step)
            status_obj.step_completed = current_steps
            await self.db.flush()
        return status_obj

    async def complete_onboarding(self, restaurant_id: UUID) -> OnboardingCompleteResponse:
        """Finalize restaurant onboarding and generate links hub."""
        status_obj = await self.get_or_create_onboarding_status(restaurant_id)
        status_obj.is_complete = True
        status_obj.completed_at = datetime.utcnow()

        rest_stmt = select(Restaurant).where(Restaurant.id == restaurant_id)
        rest_res = await self.db.execute(rest_stmt)
        restaurant = rest_res.scalar_one_or_none()
        if not restaurant:
            raise HTTPException(status_code=404, detail="Restaurant not found")

        restaurant.is_onboarded = True
        await self.db.flush()

        branches = await self.list_branches(restaurant_id)
        branch_links = [
            {"name": b.name, "url": f"https://{restaurant.slug}.platelink.africa/{b.name.lower().replace(' ', '-')}"}
            for b in branches
        ]

        return OnboardingCompleteResponse(
            restaurant_id=restaurant_id,
            slug=restaurant.slug,
            primary_link=f"https://{restaurant.slug}.platelink.africa",
            branch_links=branch_links,
            qr_download_url=f"/api/v1/tables/qr/download-all?restaurant_id={restaurant_id}",
            dashboard_url=f"/dashboard",
            staff_invite_summary={"invited": 0, "status": "active"}
        )

    # Branches CRUD
    async def list_branches(self, restaurant_id: UUID) -> List[Branch]:
        stmt = select(Branch).where(Branch.restaurant_id == restaurant_id)
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def create_branch(self, restaurant_id: UUID, data: BranchCreate) -> Branch:
        branch = Branch(
            restaurant_id=restaurant_id,
            name=data.name,
            address=data.address,
            city=data.city,
            phone=data.phone,
            email=data.email
        )
        self.db.add(branch)
        await self.db.flush()
        return branch

    async def update_branch(self, branch_id: UUID, restaurant_id: UUID, data: BranchUpdate) -> Branch:
        stmt = select(Branch).where(Branch.id == branch_id, Branch.restaurant_id == restaurant_id)
        res = await self.db.execute(stmt)
        branch = res.scalar_one_or_none()
        if not branch:
            raise HTTPException(status_code=404, detail="Branch not found")

        if data.name is not None:
            branch.name = data.name
        if data.address is not None:
            branch.address = data.address
        if data.city is not None:
            branch.city = data.city
        if data.phone is not None:
            branch.phone = data.phone
        if data.email is not None:
            branch.email = data.email
        if data.manager_id is not None:
            branch.manager_id = data.manager_id
        if data.is_active is not None:
            branch.is_active = data.is_active

        await self.db.flush()
        return branch

    async def delete_branch(self, branch_id: UUID, restaurant_id: UUID) -> bool:
        stmt = delete(Branch).where(Branch.id == branch_id, Branch.restaurant_id == restaurant_id)
        res = await self.db.execute(stmt)
        await self.db.flush()
        return res.rowcount > 0

    # Brand Settings
    async def get_or_create_brand_settings(self, restaurant_id: UUID) -> BrandSettings:
        stmt = select(BrandSettings).where(BrandSettings.restaurant_id == restaurant_id)
        res = await self.db.execute(stmt)
        bs = res.scalar_one_or_none()
        if not bs:
            bs = BrandSettings(restaurant_id=restaurant_id)
            self.db.add(bs)
            await self.db.flush()
        return bs

    async def update_brand_settings(self, restaurant_id: UUID, data: BrandSettingsUpdate) -> BrandSettings:
        bs = await self.get_or_create_brand_settings(restaurant_id)
        if data.logo_url is not None:
            bs.logo_url = data.logo_url
        if data.hero_image_url is not None:
            bs.hero_image_url = data.hero_image_url
        if data.primary_color is not None:
            bs.primary_color = data.primary_color
        if data.secondary_color is not None:
            bs.secondary_color = data.secondary_color
        if data.theme_id is not None:
            bs.theme_id = data.theme_id
        if data.custom_css is not None:
            bs.custom_css = data.custom_css

        await self.db.flush()
        return bs
