"""Role Assignment API Endpoints."""
from typing import List, Any, Dict
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.core.dependencies import require_permission
from app.services.permission_service import PermissionService
from app.services.role_service import RoleService
from app.schemas.role import RoleResponse
from app.models.staff import Staff

router = APIRouter(prefix="/assignments", tags=["assignments"])

@router.post("/users/{user_id}/roles/{role_id}", status_code=status.HTTP_201_CREATED)
async def assign_role_to_user(
    user_id: UUID,
    role_id: UUID,
    current_user = Depends(require_permission("manage_roles")),
    db: AsyncSession = Depends(get_db)
):
    """Assign a role to a user."""
    p_service = PermissionService(db)
    r_service = RoleService(db)

    # Validate staff existence
    staff_res = await db.execute(select(Staff).where(Staff.id == user_id))
    staff = staff_res.scalar_one_or_none()
    if not staff:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User/Staff not found")

    # Validate role existence
    role = await r_service.get_role(role_id)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")

    assigned_by_id = getattr(current_user, "id", None)
    assigned = await p_service.assign_role_to_user(user_id=user_id, role_id=role_id, assigned_by=assigned_by_id)
    if not assigned:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already has this role")

    return {"detail": f"Role '{role.name}' assigned to user successfully"}

@router.delete("/users/{user_id}/roles/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_role_from_user(
    user_id: UUID,
    role_id: UUID,
    current_user = Depends(require_permission("manage_roles")),
    db: AsyncSession = Depends(get_db)
):
    """Remove a role assignment from a user."""
    p_service = PermissionService(db)
    r_service = RoleService(db)

    role = await r_service.get_role(role_id)
    if role and role.name == "Owner":
        # Ensure we don't remove the last owner
        owners = await p_service.get_users_with_role(role_id)
        if len(owners) <= 1 and any(o.id == user_id for o in owners):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove the last Owner role assignment"
            )

    removed = await p_service.remove_role_from_user(user_id=user_id, role_id=role_id)
    if not removed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User role assignment not found")

@router.get("/users/{user_id}/roles", response_model=List[RoleResponse])
async def get_user_roles_assignments(
    user_id: UUID,
    current_user = Depends(require_permission("view_staff")),
    db: AsyncSession = Depends(get_db)
):
    """Get all roles assigned to a specific user."""
    p_service = PermissionService(db)
    return await p_service.get_user_roles(user_id=user_id)

@router.get("/roles/{role_id}/users", response_model=List[Dict[str, Any]])
async def get_role_users(
    role_id: UUID,
    current_user = Depends(require_permission("view_staff")),
    db: AsyncSession = Depends(get_db)
):
    """Get all users assigned to a specific role."""
    p_service = PermissionService(db)
    users = await p_service.get_users_with_role(role_id=role_id)
    return [
        {
            "id": u.id,
            "full_name": u.full_name,
            "email": u.email,
            "phone": u.phone,
            "is_active": u.is_active,
            "restaurant_id": u.restaurant_id
        }
        for u in users
    ]
