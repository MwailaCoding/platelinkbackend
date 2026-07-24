"""Role management unit tests."""
import pytest
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from apps.api.app.models.role import Role
from apps.api.app.models.permission import Permission
from apps.api.app.models.restaurant import Restaurant

@pytest.mark.asyncio
async def test_create_role(test_db: AsyncSession, sample_restaurant: Restaurant):
    """Test custom role creation."""
    role = Role(
        id=uuid.uuid4(),
        restaurant_id=sample_restaurant.id,
        name="Shift Supervisor",
        description="Oversees floor operations",
        level=50,
        is_custom=True,
        is_system=False
    )
    test_db.add(role)
    await test_db.commit()

    stmt = select(Role).where(Role.id == role.id)
    res = await test_db.execute(stmt)
    saved = res.scalar_one_or_none()
    assert saved is not None
    assert saved.name == "Shift Supervisor"
    assert saved.is_custom is True

@pytest.mark.asyncio
async def test_update_role(test_db: AsyncSession, sample_restaurant: Restaurant):
    """Test custom role updates."""
    role = Role(
        id=uuid.uuid4(),
        restaurant_id=sample_restaurant.id,
        name="Line Cook",
        level=20,
        is_custom=True
    )
    test_db.add(role)
    await test_db.commit()

    role.name = "Senior Line Cook"
    role.level = 35
    await test_db.commit()

    stmt = select(Role).where(Role.id == role.id)
    res = await test_db.execute(stmt)
    updated = res.scalar_one_or_none()
    assert updated.name == "Senior Line Cook"
    assert updated.level == 35

@pytest.mark.asyncio
async def test_delete_role(test_db: AsyncSession, sample_restaurant: Restaurant):
    """Test custom role deletion."""
    role = Role(
        id=uuid.uuid4(),
        restaurant_id=sample_restaurant.id,
        name="Temp Staff",
        is_custom=True
    )
    test_db.add(role)
    await test_db.commit()

    await test_db.delete(role)
    await test_db.commit()

    stmt = select(Role).where(Role.id == role.id)
    res = await test_db.execute(stmt)
    assert res.scalar_one_or_none() is None

@pytest.mark.asyncio
async def test_assign_permissions(test_db: AsyncSession, sample_restaurant: Restaurant, sample_permissions: list[Permission]):
    """Test assigning permissions to custom roles."""
    role = Role(
        id=uuid.uuid4(),
        restaurant_id=sample_restaurant.id,
        name="Floor Captain",
        is_custom=True,
        permissions=[]
    )
    test_db.add(role)
    await test_db.commit()

    role.permissions = sample_permissions[:2]
    await test_db.commit()

    stmt = select(Role).where(Role.id == role.id)
    res = await test_db.execute(stmt)
    loaded_role = res.scalar_one_or_none()
    assert len(loaded_role.permissions) == 2
