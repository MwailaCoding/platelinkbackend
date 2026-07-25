from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel

from app.core.deps import get_db
from models import Restaurant, RestaurantSetting
from app.core.deps import get_current_user as get_current_restaurant

router = APIRouter(tags=["Settings"])

class FloorPlanSettingsRequest(BaseModel):
    grid_size: int
    snap_enabled: bool
    show_grid: bool

def get_restaurant_setting(db: Session, restaurant_id: str, key: str, default: str) -> str:
    setting = db.query(RestaurantSetting).filter(
        RestaurantSetting.restaurant_id == restaurant_id,
        RestaurantSetting.key == key
    ).first()
    if setting and 'value' in setting.value:
        return setting.value['value']
    return default

def update_restaurant_setting(db: Session, restaurant_id: str, key: str, value: str):
    setting = db.query(RestaurantSetting).filter(
        RestaurantSetting.restaurant_id == restaurant_id,
        RestaurantSetting.key == key
    ).first()
    if setting:
        setting.value = {'value': value}
    else:
        setting = RestaurantSetting(
            restaurant_id=restaurant_id,
            key=key,
            value={'value': value}
        )
        db.add(setting)
    db.commit()

@router.get("/settings/floor-plan")
async def get_floor_plan_settings(
    db: Session = Depends(get_db),
    restaurant: Restaurant = Depends(get_current_restaurant)
):
    """Get floor plan editor settings"""
    
    grid_size = get_restaurant_setting(db, restaurant.id, 'floor_plan_grid_size', '20')
    snap_enabled = get_restaurant_setting(db, restaurant.id, 'floor_plan_snap_enabled', 'true')
    show_grid = get_restaurant_setting(db, restaurant.id, 'floor_plan_show_grid', 'true')
    
    return {
        "grid_size": int(grid_size),
        "snap_enabled": snap_enabled.lower() == 'true',
        "show_grid": show_grid.lower() == 'true'
    }

@router.put("/settings/floor-plan")
async def update_floor_plan_settings(
    request: FloorPlanSettingsRequest,
    db: Session = Depends(get_db),
    restaurant: Restaurant = Depends(get_current_restaurant)
):
    """Update floor plan editor settings"""
    
    update_restaurant_setting(db, restaurant.id, 'floor_plan_grid_size', str(request.grid_size))
    update_restaurant_setting(db, restaurant.id, 'floor_plan_snap_enabled', str(request.snap_enabled).lower())
    update_restaurant_setting(db, restaurant.id, 'floor_plan_show_grid', str(request.show_grid).lower())
    
    return {"success": True}
