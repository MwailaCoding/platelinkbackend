# app/core/deps.py
from typing import Generator, Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from app.core.config import settings
from app.db.session import async_session_local
from app.models import Staff, Restaurant
from sqlalchemy import select

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)

async def get_db() -> Generator:
    async with async_session_local() as session:
        yield session

async def get_redis() -> Redis:
    client = Redis.from_url(settings.REDIS_URL, decode_responses=True)
    try:
        yield client
    finally:
        await client.close()

async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(reusable_oauth2),
    redis: Redis = Depends(get_redis)
) -> Staff:
    # Check blacklist
    is_blacklisted = await redis.get(f"token_blacklist:{token}")
    if is_blacklisted:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is revoked",
        )
        
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        staff_id: str = payload.get("sub")
        if staff_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
    
    result = await db.execute(select(Staff).where(Staff.id == staff_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user

async def get_current_active_staff(
    current_user: Staff = Depends(get_current_user),
) -> Staff:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive staff")
    return current_user

def check_role(roles: list):
    async def role_checker(user: Staff = Depends(get_current_active_staff)):
        has_role = user.role.value in roles
        has_role_type = hasattr(user, 'role_type') and user.role_type in roles
        if not (has_role or has_role_type):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="The user doesn't have enough privileges",
            )
        return user
    return role_checker
