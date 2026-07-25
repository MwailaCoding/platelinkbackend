# app/schemas/payment.py
from typing import Optional
from decimal import Decimal
from uuid import UUID
from datetime import datetime
from app.schemas.base import BaseSchema
from app.models.enums import PaymentStatus, PaymentMethod

class MpesaSTKPush(BaseSchema):
    phone_number: str
    amount: Decimal
    order_id: UUID

class PaymentRead(BaseSchema):
    id: UUID
    amount: Decimal
    payment_method: PaymentMethod
    status: PaymentStatus
    created_at: datetime

# app/dependencies.py
from typing import Generator, Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from app.core.config import settings
from app.db.session import async_session_local
from app.models import Staff, Restaurant, StaffRole
from sqlalchemy import select

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)

async def get_db() -> Generator:
    async with async_session_local() as session:
        try:
            yield session
        finally:
            await session.close()

async def get_redis() -> Redis:
    client = Redis.from_url(settings.REDIS_URL, decode_responses=True)
    try:
        yield client
    finally:
        await client.close()

async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(reusable_oauth2)
) -> Staff:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        staff_id: str = payload.get("sub")
        if staff_id is None:
            raise HTTPException(status_code=401, detail="Invalid credentials")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    result = await db.execute(select(Staff).where(Staff.id == staff_id))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    return user

async def get_current_restaurant(
    current_user: Staff = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Restaurant:
    restaurant = await db.get(Restaurant, current_user.restaurant_id)
    if not restaurant or not restaurant.is_active:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    return restaurant

def get_staff_with_role(roles: list):
    async def role_checker(user: Staff = Depends(get_current_user)):
        if user.role.value not in roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return role_checker
