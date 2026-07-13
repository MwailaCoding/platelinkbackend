# tests/test_staff.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import HTTPException
from app.api.v1.endpoints.staff import bulk_create_staff
from app.schemas import schemas

@pytest.mark.asyncio
async def test_bulk_create_staff_raw_list():
    """
    Test bulk staff creation with a raw list of StaffCreate schemas.
    """
    db = AsyncMock()
    db.add = MagicMock()
    current_user = MagicMock()
    current_user.restaurant_id = "test_restaurant_uuid"
    
    data = [
        schemas.StaffCreate(
            full_name="John Doe",
            role="waiter",
            pin_code="1234",
            shift="morning",
            assigned_tables=[]
        ),
        schemas.StaffCreate(
            full_name="Jane Chef",
            role="chef",
            pin_code="5678",
            shift="evening",
            assigned_tables=[]
        )
    ]
    
    res = await bulk_create_staff(data=data, current_user=current_user, db=db)
    
    assert res == {"msg": "Successfully created 2 staff members"}
    assert db.add.call_count == 2
    db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_bulk_create_staff_wrapped():
    """
    Test bulk staff creation with a BulkStaffInput wrapped list.
    """
    db = AsyncMock()
    db.add = MagicMock()
    current_user = MagicMock()
    current_user.restaurant_id = "test_restaurant_uuid"
    
    data = schemas.BulkStaffInput(
        staff=[
            schemas.StaffCreate(
                full_name="Jane Doe",
                role="waiter",
                pin_code="2323",
                shift="full",
                assigned_tables=[]
            )
        ]
    )
    
    res = await bulk_create_staff(data=data, current_user=current_user, db=db)
    
    assert res == {"msg": "Successfully created 1 staff members"}
    assert db.add.call_count == 1
    db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_bulk_create_staff_duplicate_pins():
    """
    Test duplicate PIN detection during bulk staff creation.
    """
    db = AsyncMock()
    current_user = MagicMock()
    current_user.restaurant_id = "test_restaurant_uuid"
    
    data = [
        schemas.StaffCreate(
            full_name="John Doe",
            role="waiter",
            pin_code="1234",
            shift="morning",
            assigned_tables=[]
        ),
        schemas.StaffCreate(
            full_name="Jane Chef",
            role="chef",
            pin_code="1234",  # Duplicate PIN
            shift="evening",
            assigned_tables=[]
        )
    ]
    
    with pytest.raises(HTTPException) as exc_info:
        await bulk_create_staff(data=data, current_user=current_user, db=db)
        
    assert exc_info.value.status_code == 400
    assert "Duplicate PINs" in exc_info.value.detail
