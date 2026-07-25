"""Permission Service for managing user permissions and roles."""
import logging
from typing import List, Optional
from uuid import UUID
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.role import Role
from app.models.permission import Permission
from app.models.user_role import UserRole
from app.models.role_permission import RolePermission
from app.models.staff import Staff
from app.core.cache import permission_cache

logger = logging.getLogger(__name__)

class PermissionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_permissions(self, user_id: UUID) -> List[str]:
        """Get all permission names assigned to a user."""
        user_id_str = str(user_id)
        cached = permission_cache.get(user_id_str)
        if cached is not None:
            return cached

        stmt = (
            select(Permission.name)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .join(UserRole, UserRole.role_id == RolePermission.role_id)
            .where(UserRole.user_id == user_id)
            .distinct()
        )
        result = await self.db.execute(stmt)
        permissions = list(result.scalars().all())
        permission_cache.set(user_id_str, permissions)
        return permissions

    async def get_user_roles(self, user_id: UUID) -> List[Role]:
        """Get all roles assigned to a user."""
        stmt = (
            select(Role)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(UserRole.user_id == user_id)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def assign_role_to_user(self, user_id: UUID, role_id: UUID, assigned_by: Optional[UUID] = None) -> bool:
        """Assign a role to a user."""
        stmt = select(UserRole).where(UserRole.user_id == user_id, UserRole.role_id == role_id)
        res = await self.db.execute(stmt)
        existing = res.scalar_one_or_none()
        if not existing:
            ur = UserRole(user_id=user_id, role_id=role_id, assigned_by=assigned_by)
            self.db.add(ur)
            await self.db.flush()
            permission_cache.clear(str(user_id))
            return True
        return False

    async def remove_role_from_user(self, user_id: UUID, role_id: UUID) -> bool:
        """Remove a role from a user."""
        stmt = delete(UserRole).where(UserRole.user_id == user_id, UserRole.role_id == role_id)
        result = await self.db.execute(stmt)
        await self.db.flush()
        permission_cache.clear(str(user_id))
        return result.rowcount > 0

    async def get_users_with_role(self, role_id: UUID) -> List[Staff]:
        """Get all users assigned to a specific role."""
        stmt = (
            select(Staff)
            .join(UserRole, UserRole.user_id == Staff.id)
            .where(UserRole.role_id == role_id)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def check_permission(self, user_id: UUID, permission_name: str) -> bool:
        """Check if user has a specific permission."""
        perms = await self.get_user_permissions(user_id)
        return permission_name in perms

    async def sync_user_permissions(self, user_id: UUID) -> None:
        """Invalidate and refresh permissions cache for a user."""
        permission_cache.clear(str(user_id))
        await self.get_user_permissions(user_id)
