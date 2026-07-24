"""Branch service layer for multi-location operations."""
import logging
from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from fastapi import HTTPException, status

from apps.api.app.models.branch import Branch
from apps.api.app.models.restaurant import Restaurant
from apps.api.app.models.user import User
from apps.api.app.schemas.branch import BranchCreate, BranchUpdate, RestaurantConfigUpdate

logger = logging.getLogger(__name__)

class BranchService:
    @staticmethod
    async def create_branch(
        db: AsyncSession,
        restaurant_id: UUID,
        data: BranchCreate
    ) -> Branch:
        """Create a new restaurant branch location."""
        # Check name uniqueness per restaurant
        stmt = select(Branch).where(
            Branch.restaurant_id == restaurant_id,
            Branch.name == data.name
        )
        res = await db.execute(stmt)
        if res.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Branch with name '{data.name}' already exists in this restaurant."
            )

        branch = Branch(
            restaurant_id=restaurant_id,
            name=data.name,
            address=data.address,
            city=data.city,
            phone=data.phone,
            email=data.email,
            manager_id=data.manager_id,
            is_active=data.is_active
        )
        db.add(branch)
        await db.commit()
        await db.refresh(branch)

        # Update restaurant multi-branch flag if > 1 branch
        stmt_count = select(Branch).where(Branch.restaurant_id == restaurant_id)
        res_count = await db.execute(stmt_count)
        branches = res_count.scalars().all()
        if len(branches) > 1:
            await db.execute(
                update(Restaurant)
                .where(Restaurant.id == restaurant_id)
                .values(is_multi_branch=True)
            )
            await db.commit()

        return branch

    @staticmethod
    async def get_branch(
        db: AsyncSession,
        branch_id: UUID,
        restaurant_id: UUID
    ) -> Optional[Branch]:
        """Get branch by ID scoped to restaurant."""
        stmt = select(Branch).where(
            Branch.id == branch_id,
            Branch.restaurant_id == restaurant_id
        )
        res = await db.execute(stmt)
        branch = res.scalar_one_or_none()
        if not branch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Branch location not found."
            )
        return branch

    @staticmethod
    async def list_branches(
        db: AsyncSession,
        restaurant_id: UUID
    ) -> List[Branch]:
        """List all branches for a restaurant."""
        stmt = select(Branch).where(Branch.restaurant_id == restaurant_id).order_by(Branch.name)
        res = await db.execute(stmt)
        return res.scalars().all()

    @staticmethod
    async def update_branch(
        db: AsyncSession,
        branch_id: UUID,
        restaurant_id: UUID,
        data: BranchUpdate
    ) -> Branch:
        """Update branch details."""
        branch = await BranchService.get_branch(db, branch_id, restaurant_id)

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(branch, key, value)

        await db.commit()
        await db.refresh(branch)
        return branch

    @staticmethod
    async def delete_branch(
        db: AsyncSession,
        branch_id: UUID,
        restaurant_id: UUID
    ) -> bool:
        """Deactivate or delete branch location."""
        branch = await BranchService.get_branch(db, branch_id, restaurant_id)
        branch.is_active = False
        await db.commit()
        return True

    @staticmethod
    async def switch_user_branch(
        db: AsyncSession,
        user_id: UUID,
        restaurant_id: UUID,
        target_branch_id: UUID
    ) -> User:
        """Switch active branch for user session."""
        # Verify target branch belongs to restaurant
        await BranchService.get_branch(db, target_branch_id, restaurant_id)

        stmt = select(User).where(User.id == user_id, User.restaurant_id == restaurant_id)
        res = await db.execute(stmt)
        user = res.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found."
            )

        user.branch_id = target_branch_id
        await db.commit()
        await db.refresh(user)
        return user
