"""Staff user management unit tests."""
import pytest
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from apps.api.app.models.user import User
from apps.api.app.models.role import Role
from apps.api.app.models.restaurant import Restaurant
from apps.api.app.models.enums import UserStatus
from apps.api.app.core.auth import hash_password

@pytest.mark.asyncio
async def test_invite_staff(test_db: AsyncSession, sample_restaurant: Restaurant, sample_role: Role):
    """Test staff invitation creating PENDING user."""
    invited = User(
        id=uuid.uuid4(),
        email="newstaff@testbistro.com",
        first_name="Alice",
        last_name="Johnson",
        password_hash=hash_password("TempPassword!"),
        role_id=sample_role.id,
        restaurant_id=sample_restaurant.id,
        pin="4321",
        status=UserStatus.PENDING
    )
    test_db.add(invited)
    await test_db.commit()

    stmt = select(User).where(User.id == invited.id)
    res = await test_db.execute(stmt)
    user = res.scalar_one_or_none()
    assert user is not None
    assert user.status == UserStatus.PENDING
    assert user.email == "newstaff@testbistro.com"

@pytest.mark.asyncio
async def test_accept_invite(test_db: AsyncSession, sample_restaurant: Restaurant, sample_role: Role):
    """Test accepting invitation updates status to ACTIVE."""
    user = User(
        id=uuid.uuid4(),
        email="pending@testbistro.com",
        first_name="Bob",
        last_name="Marley",
        password_hash="temp_hash",
        role_id=sample_role.id,
        restaurant_id=sample_restaurant.id,
        status=UserStatus.PENDING
    )
    test_db.add(user)
    await test_db.commit()

    # User sets password and accepts invite
    user.password_hash = hash_password("NewPermanentPassword123!")
    user.status = UserStatus.ACTIVE
    await test_db.commit()

    stmt = select(User).where(User.id == user.id)
    res = await test_db.execute(stmt)
    active_user = res.scalar_one_or_none()
    assert active_user.status == UserStatus.ACTIVE

@pytest.mark.asyncio
async def test_activate_user(test_db: AsyncSession, sample_user: User):
    """Test activating user."""
    sample_user.status = UserStatus.INACTIVE
    await test_db.commit()

    sample_user.status = UserStatus.ACTIVE
    await test_db.commit()

    stmt = select(User).where(User.id == sample_user.id)
    res = await test_db.execute(stmt)
    assert res.scalar_one_or_none().status == UserStatus.ACTIVE

@pytest.mark.asyncio
async def test_deactivate_user(test_db: AsyncSession, sample_user: User):
    """Test deactivating staff user."""
    sample_user.status = UserStatus.INACTIVE
    await test_db.commit()

    stmt = select(User).where(User.id == sample_user.id)
    res = await test_db.execute(stmt)
    assert res.scalar_one_or_none().status == UserStatus.INACTIVE
