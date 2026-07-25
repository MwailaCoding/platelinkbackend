"""Core permission checking utilities and helper functions."""
import logging
from typing import List, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.role import Role
from app.models.permission import Permission
from app.models.user_role import UserRole
from app.models.role_permission import RolePermission
from app.core.cache import permission_cache

logger = logging.getLogger(__name__)

def is_owner(user: Any) -> bool:
    """Check if the user has an Owner role."""
    role_val = getattr(user, 'role', None)
    role_str = str(role_val.value if hasattr(role_val, 'value') else role_val).lower()
    role_type = str(getattr(user, 'role_type', '')).lower()
    return role_str == 'owner' or role_type == 'owner'

def is_manager(user: Any) -> bool:
    """Check if the user has a Manager role."""
    role_val = getattr(user, 'role', None)
    role_str = str(role_val.value if hasattr(role_val, 'value') else role_val).lower()
    role_type = str(getattr(user, 'role_type', '')).lower()
    return is_owner(user) or role_str == 'manager' or role_type == 'manager'

async def get_user_roles(user: Any, db: AsyncSession) -> List[Role]:
    """Get all assigned Role objects for a user."""
    user_id = getattr(user, 'id', None)
    if not user_id:
        return []
    
    stmt = (
        select(Role)
        .join(UserRole, UserRole.role_id == Role.id)
        .where(UserRole.user_id == user_id)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())

async def get_user_permissions(user: Any, db: AsyncSession) -> List[str]:
    """Get all permission names for a user, with caching support."""
    user_id_str = str(getattr(user, 'id', ''))
    
    # 1. Check in-memory cache
    cached = permission_cache.get(user_id_str)
    if cached is not None:
        return cached

    # 2. Owners automatically have all permissions
    if is_owner(user):
        stmt_all = select(Permission.name)
        res_all = await db.execute(stmt_all)
        all_perms = list(res_all.scalars().all())
        permission_cache.set(user_id_str, all_perms)
        return all_perms

    # 3. Query permissions via UserRole -> RolePermission -> Permission
    user_id = getattr(user, 'id', None)
    stmt = (
        select(Permission.name)
        .join(RolePermission, RolePermission.permission_id == Permission.id)
        .join(UserRole, UserRole.role_id == RolePermission.role_id)
        .where(UserRole.user_id == user_id)
        .distinct()
    )
    result = await db.execute(stmt)
    permissions = list(result.scalars().all())

    # Fallback to system default role permissions if user_roles not populated yet
    if not permissions:
        role_val = getattr(user, 'role', None)
        role_name = str(role_val.value if hasattr(role_val, 'value') else role_val).capitalize()
        sys_role_stmt = (
            select(Permission.name)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .join(Role, Role.id == RolePermission.role_id)
            .where(Role.name == role_name, Role.restaurant_id.is_(None))
        )
        sys_res = await db.execute(sys_role_stmt)
        permissions = list(sys_res.scalars().all())

    permission_cache.set(user_id_str, permissions)
    return permissions

async def has_permission(user: Any, permission_name: str, db: AsyncSession) -> bool:
    """Check if a user has a specific permission."""
    if is_owner(user):
        return True
    user_perms = await get_user_permissions(user, db)
    return permission_name in user_perms

async def has_any_permission(user: Any, permission_names: List[str], db: AsyncSession) -> bool:
    """Check if a user has ANY of the given permissions."""
    if is_owner(user):
        return True
    user_perms = await get_user_permissions(user, db)
    return any(p in user_perms for p in permission_names)

async def has_all_permissions(user: Any, permission_names: List[str], db: AsyncSession) -> bool:
    """Check if a user has ALL of the given permissions."""
    if is_owner(user):
        return True
    user_perms = await get_user_permissions(user, db)
    return all(p in user_perms for p in permission_names)
