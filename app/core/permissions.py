"""Permission evaluation middleware and authorization dependencies."""
import logging
from uuid import UUID
from typing import Callable, Coroutine, Any

from fastapi import Depends, HTTPException, status
from apps.api.app.models.user import User
from apps.api.app.models.enums import PermissionAction
from apps.api.app.core.auth import get_current_active_user

logger = logging.getLogger(__name__)

def has_permission(user: User, permission_name: str) -> bool:
    """Check whether a user has a specific permission by name."""
    if not user or not user.role:
        return False
    
    # System admins or roles with level >= 100 bypass granular permission checks
    if getattr(user.role, "is_system", False) and getattr(user.role, "name", "").lower() == "owner":
        return True

    user_permissions = getattr(user.role, "permissions", []) or []
    for perm in user_permissions:
        # Match exact permission name or wildcard / manage action
        if perm.name == permission_name or perm.action == PermissionAction.MANAGE:
            return True
    return False

def require_permission(permission_name: str) -> Callable[..., Coroutine[Any, Any, User]]:
    """FastAPI dependency to require a specific permission."""
    async def permission_dependency(current_user: User = Depends(get_current_active_user)) -> User:
        if not has_permission(current_user, permission_name):
            logger.warning(
                f"User {current_user.id} denied access for permission '{permission_name}'"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions: requires '{permission_name}'"
            )
        return current_user
    return permission_dependency

def has_resource_permission(user: User, resource: str, action: PermissionAction) -> bool:
    """Check whether a user has a specific resource and action permission."""
    if not user or not user.role:
        return False

    if getattr(user.role, "is_system", False) and getattr(user.role, "name", "").lower() == "owner":
        return True

    user_permissions = getattr(user.role, "permissions", []) or []
    for perm in user_permissions:
        if perm.resource == resource and (perm.action == action or perm.action == PermissionAction.MANAGE):
            return True
    return False

def has_restaurant_access(user: User, restaurant_id: UUID) -> bool:
    """Verify user belongs to the specified restaurant ID."""
    if not user:
        return False
    return user.restaurant_id == restaurant_id

def has_branch_access(user: User, branch_id: UUID) -> bool:
    """Verify user has access to a specific branch ID."""
    if not user:
        return False
    # If user has no specific branch assigned, they have restaurant-wide access
    if user.branch_id is None:
        return True
    return user.branch_id == branch_id
