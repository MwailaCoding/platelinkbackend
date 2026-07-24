"""Authentication flow unit tests."""
import pytest
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from apps.api.app.core.auth import authenticate_user, authenticate_user_pin, authenticate_user_qr
from apps.api.app.models.user import User
from apps.api.app.schemas.user import UserRegisterRequest
from apps.api.app.api.v1.endpoints.auth import register

@pytest.mark.asyncio
async def test_login_success(test_db: AsyncSession, sample_user: User):
    """Test successful email and password authentication."""
    user = await authenticate_user(test_db, email="owner@testbistro.com", password="Password123!")
    assert user is not None
    assert user.id == sample_user.id
    assert user.email == "owner@testbistro.com"

@pytest.mark.asyncio
async def test_login_failure(test_db: AsyncSession, sample_user: User):
    """Test invalid credentials failure modes."""
    # Wrong password
    user_wrong_pass = await authenticate_user(test_db, email="owner@testbistro.com", password="WrongPassword!")
    assert user_wrong_pass is None

    # Nonexistent email
    user_wrong_email = await authenticate_user(test_db, email="nonexistent@testbistro.com", password="Password123!")
    assert user_wrong_email is None

@pytest.mark.asyncio
async def test_pin_login(test_db: AsyncSession, sample_user: User):
    """Test 4-digit PIN authentication flow."""
    # Successful PIN login
    user_pin = await authenticate_user_pin(test_db, email="owner@testbistro.com", pin="1234")
    assert user_pin is not None
    assert user_pin.id == sample_user.id

    # Wrong PIN
    user_wrong_pin = await authenticate_user_pin(test_db, email="owner@testbistro.com", pin="9999")
    assert user_wrong_pin is None

@pytest.mark.asyncio
async def test_qr_login(test_db: AsyncSession, sample_user: User):
    """Test QR code authentication flow."""
    qr_payload = f"QR_USER_{sample_user.id}"
    user_qr = await authenticate_user_qr(test_db, user_id=str(sample_user.id), qr_code=qr_payload)
    assert user_qr is not None
    assert user_qr.id == sample_user.id

    # Invalid QR payload
    invalid_qr = await authenticate_user_qr(test_db, user_id=str(sample_user.id), qr_code="INVALID_QR_CODE")
    assert invalid_qr is None

@pytest.mark.asyncio
async def test_register_tenant(test_db: AsyncSession):
    """Test tenant registration endpoint logic."""
    req = UserRegisterRequest(
        restaurant_name="Savory Grill",
        subdomain="savorygrill",
        owner_name="Alice Owner",
        email="alice@savorygrill.com",
        password="Password123!",
        restaurant_size="large",
        restaurant_type="multi_branch"
    )
    res = await register(req, test_db)
    assert res.access_token is not None
    assert res.user.email == "alice@savorygrill.com"
