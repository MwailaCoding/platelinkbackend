# app/api/v1/endpoints/public.py
"""
Public endpoints that don't require authentication.
Used by the landing page and customer-facing features.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.deps import get_db
from app.models import Restaurant

router = APIRouter()

@router.get("/stats")
async def get_public_stats(db: AsyncSession = Depends(get_db)):
    """
    Returns public statistics shown on the landing page.
    No authentication required.
    """
    restaurant_count = (
        await db.execute(
            select(func.count(Restaurant.id)).where(
                Restaurant.is_active == True,
                Restaurant.deleted_at == None
            )
        )
    ).scalar() or 0

    return {
        "restaurant_count": restaurant_count,
        "platform": "PlateLink Africa",
    }
