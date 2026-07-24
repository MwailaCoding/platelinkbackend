"""Authentication API endpoints."""
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from apps.api.app.core.database import get_db
from apps.api.app.core.auth import (
    authenticate_user,
    authenticate_user_pin,
    authenticate_user_qr,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    get_current_user,
    token_blacklist,
)
from apps.api.app.schemas.user import (
    UserLogin,
    UserPINLogin,
    UserQRLogin,
    UserRegisterRequest,
    TokenResponse,
    UserResponse,
)
from apps.api.app.models.user import User
from apps.api.app.models.restaurant import Restaurant
from apps.api.app.models.branch import Branch
from apps.api.app.models.role import Role
from apps.api.app.models.enums import RestaurantSize, UserStatus

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])

async def get_user_with_role(db: AsyncSession, user_id: Any) -> User:
    """Fetch user with eager-loaded role and permissions for Pydantic serialization."""
    stmt = (
        select(User)
        .options(selectinload(User.role).selectinload(Role.permissions))
        .where(User.id == user_id)
    )
    res = await db.execute(stmt)
    return res.scalar_one()

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(data: UserRegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register a new restaurant tenant with size classification, owner user, and default branch."""
    # Check email uniqueness
    email_clean = data.email.lower().strip()
    user_stmt = select(User).where(User.email == email_clean)
    res_user = await db.execute(user_stmt)
    if res_user.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists."
        )

    # Check slug uniqueness
    slug_clean = data.subdomain.lower().strip()
    rest_stmt = select(Restaurant).where(Restaurant.slug == slug_clean)
    res_rest = await db.execute(rest_stmt)
    if res_rest.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Workspace URL / subdomain is already taken."
        )

    # Map restaurant size
    size_map = {
        "small": RestaurantSize.SMALL,
        "medium": RestaurantSize.MEDIUM,
        "large": RestaurantSize.LARGE,
        "enterprise": RestaurantSize.ENTERPRISE,
    }
    size_enum = size_map.get((data.restaurant_size or "").lower(), RestaurantSize.MEDIUM)
    is_multi = (data.restaurant_type == "multi_branch")

    # 1. Create Restaurant
    restaurant = Restaurant(
        name=data.restaurant_name.strip(),
        slug=slug_clean,
        subdomain=slug_clean,
        size=size_enum,
        is_multi_branch=is_multi
    )
    db.add(restaurant)
    await db.flush()

    # 2. Create Default Branch
    branch = Branch(
        restaurant_id=restaurant.id,
        name="Main Branch",
        is_active=True
    )
    db.add(branch)
    await db.flush()

    # 3. Get or Create Owner Role
    role_stmt = select(Role).where(
        Role.name == "Owner",
        Role.restaurant_id.is_(None)
    )
    res_role = await db.execute(role_stmt)
    owner_role = res_role.scalar_one_or_none()

    if not owner_role:
        owner_role = Role(
            name="Owner",
            description="System Owner with full access",
            level=100,
            is_system=True,
            is_custom=False
        )
        db.add(owner_role)
        await db.flush()

    # Parse Owner Name
    name_parts = (data.owner_name or "Admin").strip().split(" ", 1)
    first_name = name_parts[0]
    last_name = name_parts[1] if len(name_parts) > 1 else "Owner"

    # 4. Create Owner User
    owner_user = User(
        email=email_clean,
        phone=data.phone,
        password_hash=hash_password(data.password),
        first_name=first_name,
        last_name=last_name,
        role_id=owner_role.id,
        restaurant_id=restaurant.id,
        branch_id=branch.id,
        pin="1234",
        status=UserStatus.ACTIVE
    )
    db.add(owner_user)
    await db.commit()
    
    full_user = await get_user_with_role(db, owner_user.id)

    token_data = {"sub": str(full_user.id), "restaurant_id": str(restaurant.id)}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=UserResponse.model_validate(full_user)
    )

@router.post("/login", response_model=TokenResponse)
async def login(user_data: UserLogin, db: AsyncSession = Depends(get_db)):
    """Authenticate user with email and password."""
    user = await authenticate_user(db, email=user_data.email, password=user_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    # Update last login timestamp
    user.last_login = datetime.now(timezone.utc)
    await db.commit()
    full_user = await get_user_with_role(db, user.id)

    token_data = {"sub": str(full_user.id), "restaurant_id": str(full_user.restaurant_id)}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=UserResponse.model_validate(full_user)
    )

@router.post("/login/pin", response_model=TokenResponse)
async def login_pin(user_data: UserPINLogin, db: AsyncSession = Depends(get_db)):
    """Authenticate staff user with 4-digit PIN."""
    user = await authenticate_user_pin(db, email=user_data.email, pin=user_data.pin)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid PIN or email",
        )

    user.last_login = datetime.now(timezone.utc)
    await db.commit()
    full_user = await get_user_with_role(db, user.id)

    token_data = {"sub": str(full_user.id), "restaurant_id": str(full_user.restaurant_id)}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=UserResponse.model_validate(full_user)
    )

@router.post("/login/qr", response_model=TokenResponse)
async def login_qr(user_data: UserQRLogin, db: AsyncSession = Depends(get_db)):
    """Authenticate staff user with QR code payload."""
    user = await authenticate_user_qr(db, user_id=str(user_data.user_id), qr_code=user_data.qr_code)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid QR code payload",
        )

    user.last_login = datetime.now(timezone.utc)
    await db.commit()
    full_user = await get_user_with_role(db, user.id)

    token_data = {"sub": str(full_user.id), "restaurant_id": str(full_user.restaurant_id)}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=UserResponse.model_validate(full_user)
    )

@router.post("/logout")
async def logout(
    authorization: str = Header(...),
    current_user: User = Depends(get_current_user)
):
    """Logout current user and invalidate bearer token."""
    if authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        token_blacklist.add(token)
    return {"message": "Logged out successfully"}

@router.post("/refresh")
async def refresh_token(refresh_token: str, db: AsyncSession = Depends(get_db)):
    """Generate new access token using a valid refresh token."""
    payload = decode_token(refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type for refresh",
        )
    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token payload",
        )

    token_data = {"sub": user_id_str, "restaurant_id": payload.get("restaurant_id")}
    new_access_token = create_access_token(token_data)
    return {"access_token": new_access_token, "token_type": "bearer"}

@router.post("/forgot-password")
async def forgot_password(email: str, db: AsyncSession = Depends(get_db)):
    """Request password reset link/token."""
    stmt = select(User).where(User.email == email.lower().strip())
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()
    if not user:
        return {"message": "If an account exists, password reset instructions have been sent."}

    reset_token = create_access_token({"sub": str(user.id), "purpose": "reset_password"}, expires_delta=timedelta(hours=1))
    logger.info(f"Generated password reset token for user {user.email}: {reset_token}")
    return {"message": "If an account exists, password reset instructions have been sent.", "reset_token": reset_token}

@router.post("/reset-password")
async def reset_password(token: str, new_password: str, db: AsyncSession = Depends(get_db)):
    """Reset user password with valid reset token."""
    if len(new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long",
        )
    payload = decode_token(token)
    if payload.get("purpose") != "reset_password":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token purpose",
        )
    user_id = payload.get("sub")
    stmt = select(User).where(User.id == user_id)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    user.password_hash = hash_password(new_password)
    await db.commit()
    return {"message": "Password updated successfully"}
