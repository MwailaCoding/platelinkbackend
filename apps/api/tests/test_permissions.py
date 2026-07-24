"""Permission evaluation unit tests."""
import pytest
import uuid
from apps.api.app.core.permissions import has_permission, has_resource_permission, has_restaurant_access
from apps.api.app.models.user import User
from apps.api.app.models.role import Role
from apps.api.app.models.permission import Permission
from apps.api.app.models.enums import PermissionAction, PermissionCategory, UserStatus

@pytest.mark.asyncio
async def test_permission_allowed(sample_user: User):
    """Test permission verification when permission is granted."""
    assert has_permission(sample_user, "view_staff") is True
    assert has_permission(sample_user, "add_staff") is True

@pytest.mark.asyncio
async def test_permission_denied(sample_restaurant):
    """Test permission verification when role lacks permission."""
    restricted_role = Role(
        id=uuid.uuid4(),
        restaurant_id=sample_restaurant.id,
        name="Limited Waiter",
        permissions=[]
    )
    restricted_user = User(
        id=uuid.uuid4(),
        email="waiter@testbistro.com",
        password_hash="hash",
        first_name="Bob",
        last_name="Smith",
        role_id=restricted_role.id,
        restaurant_id=sample_restaurant.id,
        status=UserStatus.ACTIVE,
        role=restricted_role
    )

    assert has_permission(restricted_user, "add_staff") is False
    assert has_permission(restricted_user, "manage_roles") is False

@pytest.mark.asyncio
async def test_resource_access(sample_user: User, sample_restaurant):
    """Test resource action checks and restaurant access boundary."""
    # Resource action permission
    assert has_resource_permission(sample_user, "staff", PermissionAction.READ) is True
    assert has_resource_permission(sample_user, "staff", PermissionAction.CREATE) is True

    # Restaurant multitenant access
    assert has_restaurant_access(sample_user, sample_restaurant.id) is True
    assert has_restaurant_access(sample_user, uuid.uuid4()) is False
