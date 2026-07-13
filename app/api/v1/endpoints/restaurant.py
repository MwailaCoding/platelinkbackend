# app/api/v1/endpoints/restaurant.py
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.deps import get_db, get_current_user, check_role
from app.models import Restaurant, Staff, RestaurantSetting, ActivityLog, Category, Table, StaffRole
from app.schemas import schemas
from app.services.cloudinary import CloudinaryService
from app.tasks.celery import send_email_task

router = APIRouter()

@router.post("/upgrade-to-multi-branch")
async def upgrade_to_multi_branch(
    db: AsyncSession = Depends(get_db),
    current_staff: Staff = Depends(get_current_user)
):
    """Upgrade a single location restaurant to multi-branch"""
    
    if current_staff.role != StaffRole.owner:
        raise HTTPException(403, "Only owner can upgrade")
    
    restaurant = await db.get(Restaurant, current_staff.restaurant_id)
    if not restaurant:
        raise HTTPException(404, "Restaurant not found")
        
    if restaurant.is_multi_branch:
        raise HTTPException(400, "Already a multi-branch restaurant")
    
    # Update restaurant type
    restaurant.restaurant_type = 'multi_branch'
    restaurant.is_multi_branch = True
    
    await db.commit()
    
    return {"success": True, "message": "Upgraded to multi-branch"}

@router.get("/", response_model=List[schemas.RestaurantRead])
async def list_restaurants(
    db: AsyncSession = Depends(get_db)
):
    """
    List all active restaurants.
    """
    stmt = select(Restaurant).where(Restaurant.is_active == True, Restaurant.deleted_at == None)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/me", response_model=schemas.RestaurantRead)
async def get_my_restaurant(
    current_user: Staff = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current restaurant profile.
    """
    restaurant = await db.get(Restaurant, current_user.restaurant_id)
    if not restaurant or restaurant.deleted_at:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    return restaurant

@router.put("/me", response_model=schemas.RestaurantRead)
async def update_my_restaurant(
    data: schemas.RestaurantUpdate,
    current_user: Staff = Depends(check_role(["owner", "manager"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Update restaurant profile.
    """
    restaurant = await db.get(Restaurant, current_user.restaurant_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(restaurant, field, value)
    
    db.add(ActivityLog(
        restaurant_id=restaurant.id,
        staff_id=current_user.id,
        action="restaurant_updated"
    ))
    await db.commit()
    await db.refresh(restaurant)
    return restaurant

@router.get("/settings")
async def get_settings(
    current_user: Staff = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get restaurant settings as key-value pairs.
    """
    stmt = select(RestaurantSetting).where(RestaurantSetting.restaurant_id == current_user.restaurant_id)
    result = await db.execute(stmt)
    settings = result.scalars().all()
    return {s.key: s.value for s in settings}

@router.put("/settings")
async def update_settings(
    data: Dict[str, Any],
    current_user: Staff = Depends(check_role(["owner", "manager"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Upsert restaurant settings.
    """
    for key, value in data.items():
        stmt = select(RestaurantSetting).where(
            RestaurantSetting.restaurant_id == current_user.restaurant_id,
            RestaurantSetting.key == key
        )
        result = await db.execute(stmt)
        setting = result.scalar_one_or_none()
        
        if setting:
            setting.value = value
        else:
            db.add(RestaurantSetting(
                restaurant_id=current_user.restaurant_id,
                key=key,
                value=value
            ))
            
    db.add(ActivityLog(
        restaurant_id=current_user.restaurant_id,
        staff_id=current_user.id,
        action="settings_updated"
    ))
    await db.commit()
    return {"msg": "Settings updated"}

@router.put("/settings/course-pacing")
async def update_course_pacing_settings(
    settings: schemas.CoursePacingSettings,
    current_user: Staff = Depends(check_role(["owner", "manager"])),
    db: AsyncSession = Depends(get_db)
):
    """Update defaults for course pacing"""
    rid = current_user.restaurant_id
    
    async def upsert_setting(key, value):
        stmt = select(RestaurantSetting).where(
            RestaurantSetting.restaurant_id == rid,
            RestaurantSetting.key == key
        )
        existing = (await db.execute(stmt)).scalar_one_or_none()
        if existing:
            existing.value = {"value": value}
        else:
            db.add(RestaurantSetting(restaurant_id=rid, key=key, value={"value": value}))

    await upsert_setting("default_pacing", settings.default_pacing)
    await upsert_setting("auto_fire_delay_minutes", settings.auto_fire_delay_minutes)
    await upsert_setting("allow_mid_meal_change", settings.allow_mid_meal_change)

    db.add(ActivityLog(
        restaurant_id=rid,
        staff_id=current_user.id,
        action="pacing_settings_updated"
    ))
    
    await db.commit()
    return {"message": "Pacing settings updated successfully"}

@router.post("/onboarding/complete")
async def complete_onboarding(
    current_user: Staff = Depends(check_role(["owner"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Verify onboarding completion and activate.
    """
    rid = current_user.restaurant_id
    
    # Check menu items
    menu_count = await db.execute(select(Category).where(Category.restaurant_id == rid))
    if not menu_count.scalars().first():
        raise HTTPException(status_code=400, detail="Add at least one menu category first")
        
    # Check tables
    table_count = await db.execute(select(Table).where(Table.restaurant_id == rid))
    if not table_count.scalars().first():
        raise HTTPException(status_code=400, detail="Add at least one table first")
        
    restaurant = await db.get(Restaurant, rid)
    restaurant.is_onboarded = True
    
    send_email_task.delay(
        current_user.email,
        "Welcome to PlateLink Africa!",
        "Your restaurant is now fully set up and ready to accept orders."
    )
    
    await db.commit()
    return {"msg": "Onboarding completed"}

@router.post("/upload-logo")
async def upload_logo(
    file: UploadFile = File(...),
    current_user: Staff = Depends(check_role(["owner", "manager"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload restaurant logo to Cloudinary.
    """
    if file.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    content = await file.read()
    if len(content) > 2 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 2MB)")
        
    url = await CloudinaryService.upload_image(content)
    
    restaurant = await db.get(Restaurant, current_user.restaurant_id)
    restaurant.logo_url = url
    await db.commit()
    
    return {"url": url}

@router.post("/upload-certificate")
async def upload_certificate(
    file: UploadFile = File(...),
    current_user: Staff = Depends(check_role(["owner", "manager"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload business registration certificate to Cloudinary.
    Stored as a setting for compliance review.
    """
    if file.content_type not in ["image/jpeg", "image/png", "application/pdf"]:
        raise HTTPException(status_code=400, detail="Invalid file type (PDF, JPG, PNG only)")

    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 5MB)")

    url = await CloudinaryService.upload_image(content)

    # Store as a setting
    stmt = select(RestaurantSetting).where(
        RestaurantSetting.restaurant_id == current_user.restaurant_id,
        RestaurantSetting.key == "certificate_url"
    )
    result = await db.execute(stmt)
    setting = result.scalar_one_or_none()

    if setting:
        setting.value = url
    else:
        db.add(RestaurantSetting(
            restaurant_id=current_user.restaurant_id,
            key="certificate_url",
            value=url
        ))

    await db.commit()
    return {"url": url}


@router.get("/slug/{slug}")
async def get_restaurant_by_slug(
    slug: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Public endpoint to get restaurant info from slug (no auth needed)
    """
    stmt = select(Restaurant).where(Restaurant.slug == slug)
    result = await db.execute(stmt)
    restaurant = result.scalar_one_or_none()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    
    return {
        "id": restaurant.id,
        "name": restaurant.name,
        "slug": restaurant.slug,
        "subdomain": restaurant.subdomain
    }
