"""Staff invitation flow unit tests."""
import pytest
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from apps.api.app.services.invitation_service import InvitationService
from apps.api.app.models.user import User
from apps.api.app.models.role import Role
from apps.api.app.models.restaurant import Restaurant

@pytest.mark.asyncio
async def test_invitation_flow(test_db: AsyncSession, sample_restaurant: Restaurant, sample_role: Role, sample_user: User):
    """Test full invitation flow: creation, retrieval, and acceptance."""
    service = InvitationService(test_db)

    # 1. Create invitation
    invitation = await service.create_invitation(
        email="invitedwaiter@testbistro.com",
        restaurant_id=sample_restaurant.id,
        role_id=sample_role.id,
        invited_by=sample_user.id,
        first_name="Invited",
        last_name="Staff",
        pin="8888"
    )
    assert invitation is not None
    assert invitation.status == "pending"
    assert invitation.token is not None

    # 2. Get invitation by token
    retrieved = await service.get_invitation(invitation.token)
    assert retrieved is not None
    assert retrieved.email == "invitedwaiter@testbistro.com"

    # 3. Accept invitation
    acc_result = await service.accept_invitation(
        invitation.token,
        {
            "password": "NewStaffPassword123!",
            "first_name": "Invited",
            "last_name": "Staff",
            "pin": "8888"
        }
    )
    assert acc_result["status"] == "active"
    assert acc_result["email"] == "invitedwaiter@testbistro.com"

@pytest.mark.asyncio
async def test_cancel_invitation(test_db: AsyncSession, sample_restaurant: Restaurant, sample_role: Role, sample_user: User):
    """Test cancelling an invitation."""
    service = InvitationService(test_db)
    invitation = await service.create_invitation(
        email="cancelme@testbistro.com",
        restaurant_id=sample_restaurant.id,
        role_id=sample_role.id,
        invited_by=sample_user.id,
        first_name="Cancel",
        last_name="User",
        pin="1111"
    )

    success = await service.cancel_invitation(invitation.id, sample_restaurant.id)
    assert success is True
    assert invitation.status == "cancelled"
