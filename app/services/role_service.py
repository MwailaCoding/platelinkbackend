"""Role Service for managing roles and role-permission associations."""
import logging
from typing import List, Optional
from uuid import UUID
from sqlalchemy import select, delete, or_
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from app.models.role import Role
from app.models.permission import Permission
from app.models.role_permission import RolePermission
from app.models.user_role import UserRole
from app.core.cache import permission_cache

logger = logging.getLogger(__name__)

class RoleService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_role(
        self,
        name: str,
        restaurant_id: UUID,
        permission_ids: List[UUID],
        description: Optional[str] = None,
        level: int = 0
    ) -> Role:
        """Create a custom role with associated permissions."""
        stmt = select(Role).where(Role.restaurant_id == restaurant_id, Role.name == name)
        res = await self.db.execute(stmt)
        if res.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Role with name '{name}' already exists for this restaurant"
            )

        role = Role(
            name=name,
            description=description,
            level=level,
            is_system=False,
            is_custom=True,
            restaurant_id=restaurant_id
        )
        self.db.add(role)
        await self.db.flush()

        for p_id in permission_ids:
            rp = RolePermission(role_id=role.id, permission_id=p_id)
            self.db.add(rp)

        await self.db.flush()
        return role

    async def get_role(self, role_id: UUID, restaurant_id: Optional[UUID] = None) -> Optional[Role]:
        """Get role by ID with optional restaurant validation."""
        stmt = select(Role).where(Role.id == role_id)
        if restaurant_id:
            stmt = stmt.where(or_(Role.restaurant_id == restaurant_id, Role.restaurant_id.is_(None)))
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_roles(
        self,
        restaurant_id: UUID,
        include_system: bool = True,
        skip: int = 0,
        limit: int = 100
    ) -> List[Role]:
        """List all roles available for a restaurant."""
        if include_system:
            stmt = select(Role).where(or_(Role.restaurant_id == restaurant_id, Role.restaurant_id.is_(None)))
        else:
            stmt = select(Role).where(Role.restaurant_id == restaurant_id)
        
        stmt = stmt.offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def update_role(
        self,
        role_id: UUID,
        restaurant_id: UUID,
        name: Optional[str] = None,
        description: Optional[str] = None,
        level: Optional[int] = None,
        permission_ids: Optional[List[UUID]] = None
    ) -> Role:
        """Update a custom role and refresh permissions."""
        role = await self.get_role(role_id, restaurant_id)
        if not role:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
        if role.is_system:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="System roles cannot be modified")

        if name is not None:
            role.name = name
        if description is not None:
            role.description = description
        if level is not None:
            role.level = level

        if permission_ids is not None:
            await self.db.execute(delete(RolePermission).where(RolePermission.role_id == role_id))
            for p_id in permission_ids:
                rp = RolePermission(role_id=role_id, permission_id=p_id)
                self.db.add(rp)

        await self.db.flush()
        permission_cache.clear_all()
        return role

    async def delete_role(self, role_id: UUID, restaurant_id: UUID) -> bool:
        """Delete a custom role if not in use."""
        role = await self.get_role(role_id, restaurant_id)
        if not role:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
        if role.is_system:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="System roles cannot be deleted")

        # Check if role is assigned to any user
        user_check = select(UserRole).where(UserRole.role_id == role_id)
        res = await self.db.execute(user_check)
        if res.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete role currently assigned to staff members"
            )

        await self.db.execute(delete(RolePermission).where(RolePermission.role_id == role_id))
        await self.db.execute(delete(Role).where(Role.id == role_id))
        await self.db.flush()
        permission_cache.clear_all()
        return True

    async def get_system_roles(self) -> List[Role]:
        """Get all system template roles."""
        stmt = select(Role).where(Role.restaurant_id.is_(None))
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_role_permissions(self, role_id: UUID) -> List[Permission]:
        """Get all permissions linked to a specific role."""
        stmt = (
            select(Permission)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .where(RolePermission.role_id == role_id)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
