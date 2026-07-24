"""Pytest fixtures for async API database testing."""
import pytest
import pytest_asyncio
import uuid
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from fastapi.testclient import TestClient
from httpx import AsyncClient

from apps.api.app.models.base import Base
from apps.api.app.models.user import User
from apps.api.app.models.role import Role
from apps.api.app.models.permission import Permission
from apps.api.app.models.restaurant import Restaurant
from apps.api.app.models.enums import UserStatus, RestaurantSize, PermissionAction, PermissionCategory
from apps.api.app.core.auth import hash_password, create_access_token
from apps.api.app.core.database import get_db
from apps.api.app.main import app

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest_asyncio.fixture(scope="function")
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """Provide isolated in-memory SQLite database session for each test."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest_asyncio.fixture
async def sample_restaurant(test_db: AsyncSession) -> Restaurant:
    """Fixture providing a test restaurant."""
    rest = Restaurant(
        id=uuid.uuid4(),
        name="Test Gourmet Bistro",
        slug="test-gourmet-bistro",
        size=RestaurantSize.SMALL
    )
    test_db.add(rest)
    await test_db.commit()
    await test_db.refresh(rest)
    return rest

@pytest_asyncio.fixture
async def sample_permissions(test_db: AsyncSession) -> list[Permission]:
    """Fixture providing test permissions."""
    perms = [
        Permission(
            id=uuid.uuid4(),
            name="view_staff",
            resource="staff",
            action=PermissionAction.READ,
            category=PermissionCategory.STAFF
        ),
        Permission(
            id=uuid.uuid4(),
            name="add_staff",
            resource="staff",
            action=PermissionAction.CREATE,
            category=PermissionCategory.STAFF
        ),
        Permission(
            id=uuid.uuid4(),
            name="edit_staff",
            resource="staff",
            action=PermissionAction.UPDATE,
            category=PermissionCategory.STAFF
        ),
        Permission(
            id=uuid.uuid4(),
            name="delete_staff",
            resource="staff",
            action=PermissionAction.DELETE,
            category=PermissionCategory.STAFF
        ),
        Permission(
            id=uuid.uuid4(),
            name="manage_roles",
            resource="roles",
            action=PermissionAction.MANAGE,
            category=PermissionCategory.STAFF
        ),
        Permission(
            id=uuid.uuid4(),
            name="manage_permissions",
            resource="permissions",
            action=PermissionAction.MANAGE,
            category=PermissionCategory.STAFF
        ),
    ]
    for p in perms:
        test_db.add(p)
    await test_db.commit()
    return perms

@pytest_asyncio.fixture
async def sample_role(test_db: AsyncSession, sample_restaurant: Restaurant, sample_permissions: list[Permission]) -> Role:
    """Fixture providing a test Owner role with full permissions."""
    role = Role(
        id=uuid.uuid4(),
        restaurant_id=sample_restaurant.id,
        name="Owner",
        description="Restaurant Owner",
        level=100,
        is_system=True,
        is_custom=False,
        permissions=sample_permissions
    )
    test_db.add(role)
    await test_db.commit()
    await test_db.refresh(role)
    return role

@pytest_asyncio.fixture
async def sample_user(test_db: AsyncSession, sample_restaurant: Restaurant, sample_role: Role) -> User:
    """Fixture providing an active test user."""
    user = User(
        id=uuid.uuid4(),
        email="owner@testbistro.com",
        phone="+1234567890",
        password_hash=hash_password("Password123!"),
        first_name="Jane",
        last_name="Doe",
        role_id=sample_role.id,
        restaurant_id=sample_restaurant.id,
        pin="1234",
        status=UserStatus.ACTIVE,
        role=sample_role
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user

@pytest_asyncio.fixture
async def auth_headers(sample_user: User) -> dict:
    """Header dict containing valid Bearer access token."""
    token = create_access_token({"sub": str(sample_user.id), "restaurant_id": str(sample_user.restaurant_id)})
    return {"Authorization": f"Bearer {token}"}
