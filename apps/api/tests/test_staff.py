"""Staff management unit tests."""
import pytest
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from apps.api.app.services.staff_service import StaffService
from apps.api.app.models.user import User
from apps.api.app.models.role import Role
from apps.api.app.models.restaurant import Restaurant

@pytest.mark.asyncio
async def test_create_staff(test_db: AsyncSession, sample_restaurant: Restaurant, sample_role: Role):
    """Test staff creation with user profile."""
    service = StaffService(test_db)
    u_data = {
        "email": "newwaiter@testbistro.com",
        "phone": "+1999888777",
        "first_name": "Oliver",
        "last_name": "Twist",
        "role_id": sample_role.id,
        "pin": "5555",
        "send_invite": False
    }
    s_data = {
        "employee_id": "EMP-WAIT-01",
        "department": "Front of House",
        "position": "Server",
        "salary": 15.50
    }
    staff = await service.create_staff(sample_restaurant.id, u_data, s_data)
    assert staff is not None
    assert staff.employee_id == "EMP-WAIT-01"
    assert staff.department == "Front of House"
    assert staff.user.email == "newwaiter@testbistro.com"

@pytest.mark.asyncio
async def test_list_staff(test_db: AsyncSession, sample_restaurant: Restaurant, sample_user: User):
    """Test staff listing."""
    service = StaffService(test_db)
    # Create staff entry for sample_user
    u_data = {
        "email": "staff2@testbistro.com",
        "first_name": "Test",
        "last_name": "Staff2",
        "role_id": sample_user.role_id,
        "pin": "1111",
        "send_invite": False
    }
    await service.create_staff(sample_restaurant.id, u_data, {})

    staff_list, total = await service.list_staff(sample_restaurant.id)
    assert total >= 1
    assert len(staff_list) >= 1

@pytest.mark.asyncio
async def test_update_staff(test_db: AsyncSession, sample_restaurant: Restaurant, sample_role: Role):
    """Test staff update."""
    service = StaffService(test_db)
    u_data = {
        "email": "updatestaff@testbistro.com",
        "first_name": "Sam",
        "last_name": "Cook",
        "role_id": sample_role.id,
        "pin": "2222",
        "send_invite": False
    }
    staff = await service.create_staff(sample_restaurant.id, u_data, {"position": "Junior Chef"})

    updated = await service.update_staff(staff.id, sample_restaurant.id, {"position": "Head Chef", "salary": 25.0})
    assert updated is not None
    assert updated.position == "Head Chef"
    assert updated.salary == 25.0

@pytest.mark.asyncio
async def test_delete_staff(test_db: AsyncSession, sample_restaurant: Restaurant, sample_role: Role):
    """Test soft-deleting staff member."""
    service = StaffService(test_db)
    u_data = {
        "email": "deletestaff@testbistro.com",
        "first_name": "Tom",
        "last_name": "Riddle",
        "role_id": sample_role.id,
        "pin": "3333",
        "send_invite": False
    }
    staff = await service.create_staff(sample_restaurant.id, u_data, {})

    success = await service.delete_staff(staff.id, sample_restaurant.id)
    assert success is True
    assert staff.user.status.value == "inactive"
