"""FastAPI dependency factories for Role-Based Access Control (RBAC)."""
from typing import List, Callable
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_current_user, get_db
from app.core.permissions import (
    has_permission,
    has_any_permission,
    has_all_permissions,
    is_owner
)

def require_permission(permission_name: str) -> Callable:
    """FastAPI dependency to require a specific permission."""
    async def dependency(
        current_user = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
    ):
        allowed = await has_permission(current_user, permission_name, db)
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission_name}' required"
            )
        return current_user
    return dependency

def require_any_permission(permission_names: List[str]) -> Callable:
    """FastAPI dependency to require ANY permission in a given list."""
    async def dependency(
        current_user = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
    ):
        allowed = await has_any_permission(current_user, permission_names, db)
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"One of permissions {permission_names} required"
            )
        return current_user
    return dependency

def require_all_permissions(permission_names: List[str]) -> Callable:
    """FastAPI dependency to require ALL permissions in a given list."""
    async def dependency(
        current_user = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
    ):
        allowed = await has_all_permissions(current_user, permission_names, db)
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"All permissions {permission_names} required"
            )
        return current_user
    return dependency

def require_owner() -> Callable:
    """FastAPI dependency to require Owner role."""
    async def dependency(current_user = Depends(get_current_user)):
        if not is_owner(current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Owner privileges required"
            )
        return current_user
    return dependency
