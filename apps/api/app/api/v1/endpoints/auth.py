# app/api/v1/endpoints/auth.py
from uuid import uuid4
from datetime import timedelta, datetime
import random
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Body, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from redis.asyncio import Redis

from app.core import security
from app.core.config import settings
from app.core.deps import get_db, get_redis, get_current_user, reusable_oauth2
from app.models import Restaurant, Staff, StaffRole, ActivityLog, SubscriptionStatus
from models import Branches
from app.schemas import schemas
from app.services.email_service import BrevoEmailService
from app.services.email import EmailService

router = APIRouter()
logger = logging.getLogger(__name__)
email_service = BrevoEmailService()

@router.post("/register", response_model=schemas.RegisterResponse)
async def register(
    data: schemas.UserRegister,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)
):
    """
    Register a new restaurant and its owner.
    """
    # Check subdomain uniqueness
    stmt = select(Restaurant).where(Restaurant.subdomain == data.subdomain)
    existing = await db.execute(stmt)
    existing_restaurant = existing.scalar_one_or_none()
    
    if existing_restaurant:
        if existing_restaurant.is_active:
            raise HTTPException(status_code=400, detail="Subdomain already taken")
        else:
            # Clean up the inactive unverified restaurant & associated staff (via CASCADE)
            await db.delete(existing_restaurant)
            await db.flush()
    
    # Check email uniqueness for verified owners/managers
    email_stmt = select(Staff).where(
        Staff.email == data.email,
        Staff.is_verified == True,
        Staff.role.in_([StaffRole.owner, StaffRole.manager])
    )
    existing_email = await db.execute(email_stmt)
    if existing_email.scalars().first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create restaurant
    new_restaurant = Restaurant(
        name=data.restaurant_name,
        slug=data.subdomain,
        subdomain=data.subdomain,
        prefix=uuid4().hex[:3].upper(),
        is_active=False,
        trial_ends_at=datetime.utcnow() + timedelta(days=14),
        status=SubscriptionStatus.trial,
        restaurant_type=data.restaurant_type,
        is_multi_branch=(data.restaurant_type == 'multi_branch')
    )
    db.add(new_restaurant)
    await db.flush() # Get ID
    
    # Create owner staff (unverified initially)
    owner = Staff(
        restaurant_id=new_restaurant.id,
        full_name=data.owner_name,
        email=data.email,
        phone=data.phone,
        role=StaffRole.owner,
        pin_code=security.get_password_hash(data.password),
        is_active=True,
        is_verified=False
    )
    db.add(owner)
    
    # Generate verification OTP using email_service
    otp_code = email_service.generate_otp()
    
    # Store OTP in Redis
    await redis.setex(f"email_verification:{data.email}", 900, otp_code)
    
    # Send verification email via email_service using BackgroundTasks
    await email_service.send_verification_email(
        email=data.email,
        name=data.owner_name,
        otp_code=otp_code,
        background_tasks=background_tasks
    )
    
    await db.commit()
    return {
        "success": True,
        "message": "Verification email sent",
        "email": owner.email
    }

@router.post("/login", response_model=schemas.Token)
async def login(
    data: schemas.UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """
    Login for owners and managers.
    """
    stmt = select(Staff).where(
        Staff.email == data.email,
        Staff.role.in_([StaffRole.owner, StaffRole.manager])
    )
    result = await db.execute(stmt)
    users = result.scalars().all()
    
    user = None
    for u in users:
        if security.verify_password(data.password, u.pin_code):
            if not user:
                user = u
            else:
                # Prioritize verified / active
                if not user.is_verified and u.is_verified:
                    user = u
                elif user.is_verified == u.is_verified and not user.is_active and u.is_active:
                    user = u
                    
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive account")
        
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email first"
        )
    
    # Get restaurant
    restaurant = await db.get(Restaurant, user.restaurant_id)
    
    # Generate JWT
    access_token = security.create_access_token(
        subject=user.id,
        extra_claims={
            "restaurant_id": str(user.restaurant_id),
            "role": user.role.value
        }
    )
    
    user.last_login_at = datetime.utcnow()
    db.add(ActivityLog(
        restaurant_id=user.restaurant_id,
        staff_id=user.id,
        action="login"
    ))
    await db.commit()
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "restaurant_id": user.restaurant_id,
        "subdomain": restaurant.subdomain
    }

@router.post("/staff/login", response_model=schemas.Token)
async def staff_login(
    data: schemas.StaffLogin,
    db: AsyncSession = Depends(get_db)
):
    """
    Login for staff members using PIN code.
    """
    if data.restaurant_slug:
        stmt = select(Restaurant).where(Restaurant.slug == data.restaurant_slug)
        res = await db.execute(stmt)
        restaurant = res.scalar_one_or_none()
        if not restaurant:
            raise HTTPException(status_code=404, detail="Restaurant not found")
        restaurant_id = restaurant.id
    elif data.restaurant_id:
        restaurant_id = data.restaurant_id
        restaurant = await db.get(Restaurant, restaurant_id)
        if not restaurant:
            raise HTTPException(status_code=404, detail="Restaurant not found")
    else:
        raise HTTPException(status_code=400, detail="restaurant_id or restaurant_slug is required")

    stmt = select(Staff).where(
        Staff.restaurant_id == restaurant_id,
        Staff.is_active == True
    )
    result = await db.execute(stmt)
    staff_members = result.scalars().all()
    
    target_staff = None
    for s in staff_members:
        if security.verify_pin(data.pin_code, s.pin_code):
            target_staff = s
            break
            
    if not target_staff:
        raise HTTPException(status_code=401, detail="Invalid PIN")
    
    access_token = security.create_access_token(
        subject=target_staff.id,
        expires_delta=timedelta(hours=8),
        extra_claims={
            "restaurant_id": str(target_staff.restaurant_id),
            "role": target_staff.role.value,
            "assigned_tables": target_staff.assigned_tables
        }
    )
    
    target_staff.last_login_at = datetime.utcnow()
    db.add(ActivityLog(
        restaurant_id=target_staff.restaurant_id,
        staff_id=target_staff.id,
        action="staff_login"
    ))
    await db.commit()
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "restaurant_id": target_staff.restaurant_id,
        "subdomain": restaurant.subdomain
    }

@router.post("/staff/qr-login", response_model=schemas.Token)
async def staff_qr_login(
    data: schemas.QRLogin,
    db: AsyncSession = Depends(get_db)
):
    """
    Login for staff members using a QR code badge (contains staff ID or token).
    """
    import uuid
    from jose import jwt
    
    # Try parsing QR code as UUID first (direct staff ID)
    try:
        staff_id = uuid.UUID(data.qr_code.strip())
        stmt = select(Staff).where(Staff.id == staff_id, Staff.is_active == True)
        result = await db.execute(stmt)
        target_staff = result.scalar_one_or_none()
    except Exception:
        # If it's not a UUID, try decoding it as a JWT
        try:
            payload = jwt.decode(data.qr_code, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            staff_id_str = payload.get("sub")
            if not staff_id_str:
                raise Exception()
            staff_id = uuid.UUID(staff_id_str)
            stmt = select(Staff).where(Staff.id == staff_id, Staff.is_active == True)
            result = await db.execute(stmt)
            target_staff = result.scalar_one_or_none()
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid QR badge code")

    if not target_staff:
        raise HTTPException(status_code=404, detail="Staff member not found or inactive")
        
    restaurant = await db.get(Restaurant, target_staff.restaurant_id)
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
        
    access_token = security.create_access_token(
        subject=str(target_staff.id),
        expires_delta=timedelta(hours=8),
        extra_claims={
            "restaurant_id": str(target_staff.restaurant_id),
            "role": target_staff.role.value,
            "assigned_tables": target_staff.assigned_tables
        }
    )
    
    target_staff.last_login_at = datetime.utcnow()
    db.add(ActivityLog(
        restaurant_id=target_staff.restaurant_id,
        staff_id=target_staff.id,
        action="staff_qr_login"
    ))
    await db.commit()
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "restaurant_id": target_staff.restaurant_id,
        "subdomain": restaurant.subdomain
    }

@router.post("/verify-email")
async def verify_email(
    data: schemas.VerifyEmail,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)
):
    """
    Verify email with code from Redis.
    """
    otp_code = data.otp_code or data.code
    if not otp_code:
        raise HTTPException(status_code=400, detail="otp_code or code is required")

    stored_code = await redis.get(f"email_verification:{data.email}")
    if otp_code != "123456": # Master bypass for testing
        if not stored_code or stored_code != otp_code:
            raise HTTPException(status_code=400, detail="Invalid or expired code")
    
    # Activate restaurant and owner
    stmt = select(Staff).where(Staff.email == data.email)
    result = await db.execute(stmt)
    staff_members = result.scalars().all()
    
    # Prioritize unverified ones, most recent first
    unverified_staff = [s for s in staff_members if not s.is_verified]
    if unverified_staff:
        unverified_staff.sort(key=lambda s: s.created_at or datetime.min, reverse=True)
        staff = unverified_staff[0]
    else:
        staff = staff_members[0] if staff_members else None
    
    if staff:
        restaurant = await db.get(Restaurant, staff.restaurant_id)
        if restaurant:
            restaurant.is_active = True
            
            # If single location, create default branch
            if restaurant.restaurant_type == 'single':
                default_branch = Branches(
                    restaurant_id=restaurant.id,
                    name=f"{restaurant.name} - Main",
                    address=restaurant.address,
                    city=restaurant.city,
                    phone=restaurant.phone,
                    email=restaurant.email,
                    is_active=True,
                    is_main=True,
                    created_at=datetime.utcnow()
                )
                db.add(default_branch)
                await db.flush()
                staff.branch_id = default_branch.id
        
        staff.is_verified = True
        
        # Delete OTP from Redis
        await redis.delete(f"email_verification:{data.email}")
        await db.commit()
        
        # Send welcome email via email_service
        dashboard_url = f"https://{restaurant.subdomain}.platelink.africa/dashboard" if restaurant else "https://platelink.africa/dashboard"
        await email_service.send_welcome_email(
            email=staff.email,
            name=staff.full_name,
            restaurant_name=restaurant.name if restaurant else "your restaurant",
            dashboard_url=dashboard_url,
            background_tasks=background_tasks
        )
        
        return {"success": True, "message": "Email verified successfully"}
    
    raise HTTPException(status_code=404, detail="User not found")

@router.post("/resend-verification")
async def resend_verification(
    data: schemas.ResendVerificationRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)
):
    """
    Resend email verification OTP.
    Rate limited: max 3 attempts per hour.
    """
    email = data.email
    
    # Check rate limit in Redis
    rate_limit_key = f"email_verification_attempts:{email}"
    attempts = await redis.get(rate_limit_key)
    
    if attempts is not None and int(attempts) >= 3:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Max 3 verification attempts per hour."
        )
        
    stmt = select(Staff).where(Staff.email == email)
    result = await db.execute(stmt)
    staff_members = result.scalars().all()
    
    # Prioritize unverified ones, most recent first
    unverified_staff = [s for s in staff_members if not s.is_verified]
    if unverified_staff:
        unverified_staff.sort(key=lambda s: s.created_at or datetime.min, reverse=True)
        user = unverified_staff[0]
    else:
        user = staff_members[0] if staff_members else None
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
        
    if user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already verified"
        )
        
    # Generate new OTP
    otp_code = email_service.generate_otp()
    
    # Store in Redis
    await redis.setex(f"email_verification:{email}", 900, otp_code)
    
    # Update rate limit in Redis
    if attempts is None:
        await redis.setex(rate_limit_key, 3600, 1)
    else:
        await redis.incr(rate_limit_key)
        
    # Send verification email via email_service
    await email_service.send_verification_email(
        email=email,
        name=user.full_name,
        otp_code=otp_code,
        background_tasks=background_tasks
    )
    
    return {"success": True, "message": "Verification email resent"}

@router.post("/logout")
async def logout(
    token: str = Depends(reusable_oauth2),
    redis: Redis = Depends(get_redis)
):
    """
    Blacklist the current JWT.
    """
    # In a real app, you'd extract the exp from token and set TTL accordingly
    await redis.setex(f"token_blacklist:{token}", 86400, "1")
    return {"msg": "Logged out successfully"}

@router.post("/refresh", response_model=schemas.Token)
async def refresh_token(
    current_user: Staff = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate a new JWT for the current user.
    """
    restaurant = await db.get(Restaurant, current_user.restaurant_id)
    access_token = security.create_access_token(
        subject=current_user.id,
        extra_claims={
            "restaurant_id": str(current_user.restaurant_id),
            "role": current_user.role.value
        }
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "restaurant_id": current_user.restaurant_id,
        "subdomain": restaurant.subdomain
    }
