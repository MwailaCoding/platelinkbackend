"""Shifts and attendance unit tests."""
import pytest
import uuid
from datetime import date, time
from sqlalchemy.ext.asyncio import AsyncSession
from apps.api.app.services.staff_service import StaffService
from apps.api.app.services.shift_service import ShiftService
from apps.api.app.models.user import User
from apps.api.app.models.role import Role
from apps.api.app.models.restaurant import Restaurant

@pytest.mark.asyncio
async def test_create_and_list_shifts(test_db: AsyncSession, sample_restaurant: Restaurant, sample_role: Role):
    """Test shift scheduling and list queries."""
    staff_service = StaffService(test_db)
    shift_service = ShiftService(test_db)

    u_data = {
        "email": "shiftstaff@testbistro.com",
        "first_name": "Shift",
        "last_name": "Worker",
        "role_id": sample_role.id,
        "pin": "1234",
        "send_invite": False
    }
    staff = await staff_service.create_staff(sample_restaurant.id, u_data, {})

    today = date.today()
    shift_data = {
        "shift_date": today,
        "start_time": time(9, 0),
        "end_time": time(17, 0),
        "notes": "Morning shift"
    }
    shift = await shift_service.create_shift(staff.id, sample_restaurant.id, shift_data)
    assert shift is not None
    assert shift.staff_id == staff.id
    assert shift.status == "scheduled"

    shifts = await shift_service.list_shifts(sample_restaurant.id, today, today)
    assert len(shifts) == 1

@pytest.mark.asyncio
async def test_check_in_and_check_out(test_db: AsyncSession, sample_restaurant: Restaurant, sample_role: Role):
    """Test staff check-in and check-out attendance flow."""
    staff_service = StaffService(test_db)
    shift_service = ShiftService(test_db)

    u_data = {
        "email": "checkinstaff@testbistro.com",
        "first_name": "CheckIn",
        "last_name": "Staff",
        "role_id": sample_role.id,
        "pin": "9999",
        "send_invite": False
    }
    staff = await staff_service.create_staff(sample_restaurant.id, u_data, {})

    # Check in
    attendance = await shift_service.check_in(staff.id, sample_restaurant.id, method="pin")
    assert attendance is not None
    assert attendance.check_in is not None
    assert attendance.check_out is None

    # Check out
    checked_out = await shift_service.check_out(staff.id, sample_restaurant.id, method="pin")
    assert checked_out.check_out is not None

@pytest.mark.asyncio
async def test_shift_summary(test_db: AsyncSession, sample_restaurant: Restaurant):
    """Test daily shift summary retrieval."""
    shift_service = ShiftService(test_db)
    summary = await shift_service.get_shift_summary(sample_restaurant.id, date.today())
    assert summary is not None
    assert summary["date"] == date.today()
