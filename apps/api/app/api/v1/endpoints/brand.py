"""API endpoints for restaurant brand customization and theme management."""
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.core.dependencies import require_permission
from app.models.staff import Staff
from app.models.restaurant import Restaurant
from app.schemas.brand import (
    BrandSettingsResponse, BrandSettingsUpdate,
    ThemeResponse, ApplyThemeRequest, PreviewResponse
)
from app.services.brand_service import brand_service

brand_router = APIRouter(prefix="/brand", tags=["brand"])


@brand_router.get("/settings", response_model=BrandSettingsResponse)
async def get_brand_settings(
    current_user: Staff = Depends(require_permission("view_brand")),
    db: AsyncSession = Depends(get_db)
):
    """
    Get brand settings for current restaurant.
    """
    return await brand_service.get_brand_settings(db, current_user.restaurant_id)


@brand_router.put("/settings", response_model=BrandSettingsResponse)
async def update_brand_settings(
    data: BrandSettingsUpdate,
    current_user: Staff = Depends(require_permission("manage_brand")),
    db: AsyncSession = Depends(get_db)
):
    """
    Update brand settings for current restaurant.
    """
    return await brand_service.update_brand_settings(db, current_user.restaurant_id, data)


@brand_router.post("/upload-logo")
async def upload_logo(
    file: UploadFile = File(...),
    current_user: Staff = Depends(require_permission("manage_brand")),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload restaurant logo image to CDN and update brand settings.
    """
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be an image")

    logo_url = await brand_service.upload_logo(db, current_user.restaurant_id, file)
    return {"logo_url": logo_url, "message": "Logo uploaded successfully"}


@brand_router.post("/upload-hero")
async def upload_hero(
    file: UploadFile = File(...),
    current_user: Staff = Depends(require_permission("manage_brand")),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload restaurant hero cover image to CDN and update brand settings.
    """
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be an image")

    hero_image_url = await brand_service.upload_hero(db, current_user.restaurant_id, file)
    return {"hero_image_url": hero_image_url, "message": "Hero image uploaded successfully"}


@brand_router.post("/upload-favicon")
async def upload_favicon(
    file: UploadFile = File(...),
    current_user: Staff = Depends(require_permission("manage_brand")),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload restaurant favicon image to CDN and update brand settings.
    """
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be an image")

    favicon_url = await brand_service.upload_favicon(db, current_user.restaurant_id, file)
    return {"favicon_url": favicon_url, "message": "Favicon uploaded successfully"}


@brand_router.post("/apply-theme", response_model=BrandSettingsResponse)
async def apply_theme(
    request: ApplyThemeRequest,
    current_user: Staff = Depends(require_permission("manage_brand")),
    db: AsyncSession = Depends(get_db)
):
    """
    Apply preset theme to restaurant brand settings.
    """
    return await brand_service.apply_theme(db, current_user.restaurant_id, request.theme_id)


@brand_router.get("/preview", response_model=PreviewResponse)
async def get_preview(
    current_user: Staff = Depends(require_permission("view_brand")),
    db: AsyncSession = Depends(get_db)
):
    """
    Get live preview CSS and HTML structure for current brand settings.
    """
    settings = await brand_service.get_brand_settings(db, current_user.restaurant_id)
    css = await brand_service.generate_brand_css(db, current_user.restaurant_id)

    restaurant = await db.get(Restaurant, current_user.restaurant_id)
    subdomain = restaurant.subdomain if restaurant else "restaurant"

    html = f"""<div class="platelink-brand-preview" style="background-color: {settings.background_color}; color: {settings.text_color}; font-family: {settings.body_font};">
  <header style="background-color: {settings.secondary_color}; color: #ffffff; padding: 1.5rem;">
    {f'<img src="{settings.logo_url}" alt="Logo" style="height: 40px;" />' if settings.logo_url else f'<h1 style="color: {settings.primary_color}; font-family: {settings.heading_font};">{restaurant.name if restaurant else "Menu"}</h1>'}
    {f'<p>{settings.tagline}</p>' if settings.tagline else ''}
  </header>
  <main style="padding: 2rem;">
    <button style="background-color: {settings.primary_color}; color: #ffffff; padding: 0.75rem 1.5rem; border: none; border-radius: 8px;">Order Now</button>
  </main>
</div>"""

    preview_url = f"https://{subdomain}.platelink.app?preview=true"

    return PreviewResponse(
        css=css,
        html=html,
        preview_url=preview_url
    )


@brand_router.post("/publish", response_model=BrandSettingsResponse)
async def publish_changes(
    current_user: Staff = Depends(require_permission("manage_brand")),
    db: AsyncSession = Depends(get_db)
):
    """
    Publish draft brand customizations and set brand settings to active.
    """
    settings = await brand_service.get_brand_settings(db, current_user.restaurant_id)
    settings.is_active = True
    await db.commit()
    await db.refresh(settings)
    return settings


@brand_router.get("/themes", response_model=List[ThemeResponse])
async def list_themes(
    current_user: Staff = Depends(require_permission("view_brand")),
    db: AsyncSession = Depends(get_db)
):
    """
    List all available theme presets.
    """
    return await brand_service.list_themes(db)


@brand_router.get("/themes/{theme_id}", response_model=ThemeResponse)
async def get_theme(
    theme_id: UUID,
    current_user: Staff = Depends(require_permission("view_brand")),
    db: AsyncSession = Depends(get_db)
):
    """
    Get details of a specific theme preset.
    """
    return await brand_service.get_theme(db, theme_id)
