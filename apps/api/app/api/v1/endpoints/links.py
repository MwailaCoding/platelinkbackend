"""Links API router for managing restaurant links, custom domains, and staff access points."""
from typing import List, Optional
from uuid import UUID
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, get_current_user
from app.core.dependencies import require_permission
from app.models.staff import Staff
from app.schemas.link import (
    LinkCreate, LinkUpdate, LinkResponse, StaffAccessLinks, 
    CustomDomainRequest, CustomDomainResponse
)
from app.schemas.analytics import AnalyticsSummary
from app.services.link_service import link_service

links_router = APIRouter(prefix="/links", tags=["links"])

@links_router.get("/", response_model=List[LinkResponse])
async def list_links(
    db: AsyncSession = Depends(get_db),
    current_user: Staff = Depends(require_permission("view_links"))
):
    """List all links for the restaurant."""
    return await link_service.get_links(db, current_user.restaurant_id)

@links_router.get("/staff-access", response_model=StaffAccessLinks)
async def get_staff_access_links(
    db: AsyncSession = Depends(get_db),
    current_user: Staff = Depends(require_permission("view_links"))
):
    """Get staff access URLs for waiter, kitchen, and cashier."""
    return await link_service.get_staff_access_links(db, current_user.restaurant_id)

@links_router.get("/primary", response_model=LinkResponse)
async def get_primary_link(
    db: AsyncSession = Depends(get_db),
    current_user: Staff = Depends(require_permission("view_links"))
):
    """Get primary menu link."""
    primary = await link_service.get_primary_link(db, current_user.restaurant_id)
    if not primary:
        raise HTTPException(status_code=404, detail="Primary link not configured")
    return primary

@links_router.get("/custom-domain", response_model=Optional[CustomDomainResponse])
async def get_custom_domain(
    db: AsyncSession = Depends(get_db),
    current_user: Staff = Depends(require_permission("manage_links"))
):
    """Get custom domain configuration."""
    domain_info = await link_service.get_custom_domain(db, current_user.restaurant_id)
    if not domain_info:
        return None
    return domain_info

@links_router.get("/{id}", response_model=LinkResponse)
async def get_link(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Staff = Depends(require_permission("view_links"))
):
    """Get link details by ID."""
    link_obj = await link_service.get_link(db, id, current_user.restaurant_id)
    if not link_obj:
        raise HTTPException(status_code=404, detail="Link not found")
    return link_obj

@links_router.post("/", response_model=LinkResponse, status_code=status.HTTP_201_CREATED)
async def create_link(
    data: LinkCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Staff = Depends(require_permission("manage_links"))
):
    """Create a new link."""
    return await link_service.create_link(db, current_user.restaurant_id, data)

@links_router.put("/{id}", response_model=LinkResponse)
async def update_link(
    id: UUID,
    data: LinkUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Staff = Depends(require_permission("manage_links"))
):
    """Update link details."""
    try:
        return await link_service.update_link(db, id, current_user.restaurant_id, data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@links_router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_link(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Staff = Depends(require_permission("manage_links"))
):
    """Delete a link."""
    success = await link_service.delete_link(db, id, current_user.restaurant_id)
    if not success:
        raise HTTPException(status_code=404, detail="Link not found")

@links_router.post("/verify-domain", response_model=CustomDomainResponse)
async def verify_custom_domain(
    payload: CustomDomainRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Staff = Depends(require_permission("manage_links"))
):
    """Verify custom domain CNAME record."""
    return await link_service.verify_custom_domain(db, current_user.restaurant_id, payload.domain)

@links_router.put("/update-domain", response_model=CustomDomainResponse)
async def update_custom_domain(
    payload: CustomDomainRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Staff = Depends(require_permission("manage_links"))
):
    """Update custom domain configuration."""
    return await link_service.update_custom_domain(db, current_user.restaurant_id, payload.domain)

@links_router.get("/{id}/analytics", response_model=AnalyticsSummary)
async def get_link_analytics(
    id: UUID,
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: Staff = Depends(require_permission("view_links"))
):
    """Get link performance analytics within a date range."""
    return await link_service.get_link_analytics(db, id, start_date, end_date)
