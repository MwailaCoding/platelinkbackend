# app/api/v1/endpoints/kitchen_admin.py
from typing import List, Optional
from datetime import datetime, timedelta
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Body, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func, update
from app.core.deps import get_db, check_role
from app.models import (
    Staff, KitchenStation, StationPrepTime, KitchenRoutingRule,
    KitchenDisplaySetting, MenuItem, Order, OrderItem, OrderStatus, RestaurantSetting
)
from app.schemas import schemas

router = APIRouter()

# --- STATIONS ---

@router.get("/stations", response_model=List[schemas.KitchenStationRead])
async def list_stations(
    current_user: Staff = Depends(check_role(["owner", "manager", "chef"])),
    db: AsyncSession = Depends(get_db)
):
    """List all kitchen stations for the restaurant."""
    stmt = select(KitchenStation).where(
        KitchenStation.restaurant_id == current_user.restaurant_id
    ).order_by(KitchenStation.display_order.asc())
    result = await db.execute(stmt)
    stations = result.scalars().all()
    
    # Auto-create "Main Kitchen" if no stations exist
    if not stations:
        main_station = KitchenStation(
            restaurant_id=current_user.restaurant_id,
            name="Main Kitchen",
            display_name="Main Kitchen",
            station_type="hot",
            display_order=0,
            is_active=True
        )
        db.add(main_station)
        await db.commit()
        await db.refresh(main_station)
        
        # Also auto-create display settings for the main station
        default_settings = KitchenDisplaySetting(
            restaurant_id=current_user.restaurant_id,
            station_id=main_station.id,
            sound_alerts_enabled=True,
            new_order_volume=70,
            ready_order_volume=80,
            theme="dark",
            font_size="large",
            show_timer=True,
            show_modifiers=True,
            auto_accept=False,
            prep_time_buffer_percent=10
        )
        db.add(default_settings)
        await db.commit()
        
        stations = [main_station]
        
    return stations


@router.post("/stations", response_model=schemas.KitchenStationRead, status_code=status.HTTP_201_CREATED)
async def create_station(
    station_in: schemas.KitchenStationCreate,
    current_user: Staff = Depends(check_role(["owner", "manager"])),
    db: AsyncSession = Depends(get_db)
):
    """Create a new kitchen station and its default display settings."""
    station = KitchenStation(
        restaurant_id=current_user.restaurant_id,
        name=station_in.name,
        display_name=station_in.display_name or station_in.name,
        station_type=station_in.station_type,
        display_order=station_in.display_order,
        is_active=station_in.is_active
    )
    db.add(station)
    await db.commit()
    await db.refresh(station)

    # Initialize default display settings for this station
    display_settings = KitchenDisplaySetting(
        restaurant_id=current_user.restaurant_id,
        station_id=station.id,
        sound_alerts_enabled=True,
        new_order_volume=70,
        ready_order_volume=80,
        theme="dark",
        font_size="large",
        show_timer=True,
        show_modifiers=True,
        auto_accept=False,
        prep_time_buffer_percent=10
    )
    db.add(display_settings)
    
    # Initialize default prep times for this station across categories
    categories = ['appetizer', 'main', 'dessert', 'beverage']
    for cat in categories:
        prep_time = StationPrepTime(
            restaurant_id=current_user.restaurant_id,
            station_id=station.id,
            item_category=cat,
            default_seconds=300 if cat in ['appetizer', 'beverage'] else 600
        )
        db.add(prep_time)
        
    await db.commit()
    return station


@router.put("/stations/{station_id}", response_model=schemas.KitchenStationRead)
async def update_station(
    station_id: UUID,
    station_in: schemas.KitchenStationUpdate,
    current_user: Staff = Depends(check_role(["owner", "manager"])),
    db: AsyncSession = Depends(get_db)
):
    """Update kitchen station."""
    station = await db.get(KitchenStation, station_id)
    if not station or station.restaurant_id != current_user.restaurant_id:
        raise HTTPException(status_code=404, detail="Station not found")
        
    update_data = station_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(station, field, value)
        
    await db.commit()
    await db.refresh(station)
    return station


@router.delete("/stations/{station_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_station(
    station_id: UUID,
    current_user: Staff = Depends(check_role(["owner", "manager"])),
    db: AsyncSession = Depends(get_db)
):
    """Delete kitchen station and cascade nullify menu items & staff assignments."""
    station = await db.get(KitchenStation, station_id)
    if not station or station.restaurant_id != current_user.restaurant_id:
        raise HTTPException(status_code=404, detail="Station not found")
        
    # Cascade nullify staff assignments
    await db.execute(
        update(Staff)
        .where(Staff.kitchen_station_id == station_id)
        .values(kitchen_station_id=None, kitchen_station=None)
    )
    
    # Cascade nullify menu items
    await db.execute(
        update(MenuItem)
        .where(MenuItem.station_id == station_id)
        .values(station_id=None)
    )

    await db.delete(station)
    await db.commit()
    return None


# --- STATION SETTINGS ---

@router.get("/stations/{station_id}/settings", response_model=schemas.KitchenDisplaySettingRead)
async def get_station_settings(
    station_id: UUID,
    current_user: Staff = Depends(check_role(["owner", "manager", "chef"])),
    db: AsyncSession = Depends(get_db)
):
    """Get display settings for a station."""
    stmt = select(KitchenDisplaySetting).where(
        KitchenDisplaySetting.restaurant_id == current_user.restaurant_id,
        KitchenDisplaySetting.station_id == station_id
    )
    res = await db.execute(stmt)
    settings = res.scalar_one_or_none()
    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found for this station")
    return settings


@router.put("/stations/{station_id}/settings", response_model=schemas.KitchenDisplaySettingRead)
async def update_station_settings(
    station_id: UUID,
    settings_in: schemas.KitchenDisplaySettingUpdate,
    current_user: Staff = Depends(check_role(["owner", "manager", "chef"])),
    db: AsyncSession = Depends(get_db)
):
    """Update display settings for a station."""
    stmt = select(KitchenDisplaySetting).where(
        KitchenDisplaySetting.restaurant_id == current_user.restaurant_id,
        KitchenDisplaySetting.station_id == station_id
    )
    res = await db.execute(stmt)
    settings = res.scalar_one_or_none()
    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found for this station")

    update_data = settings_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(settings, field, value)

    await db.commit()
    await db.refresh(settings)
    return settings


# --- PREP TIMES ---

@router.get("/prep-times", response_model=List[schemas.StationPrepTimeRead])
async def list_prep_times(
    current_user: Staff = Depends(check_role(["owner", "manager", "chef"])),
    db: AsyncSession = Depends(get_db)
):
    """Get prep times list for all stations."""
    stmt = select(StationPrepTime).where(
        StationPrepTime.restaurant_id == current_user.restaurant_id
    )
    res = await db.execute(stmt)
    return res.scalars().all()


@router.put("/prep-times", response_model=List[schemas.StationPrepTimeRead])
async def update_prep_times(
    prep_times: List[schemas.StationPrepTimeCreate],
    current_user: Staff = Depends(check_role(["owner", "manager"])),
    db: AsyncSession = Depends(get_db)
):
    """Bulk update or create station prep times."""
    result = []
    for pt_in in prep_times:
        stmt = select(StationPrepTime).where(
            StationPrepTime.restaurant_id == current_user.restaurant_id,
            StationPrepTime.station_id == pt_in.station_id,
            StationPrepTime.item_category == pt_in.item_category
        )
        res = await db.execute(stmt)
        pt = res.scalar_one_or_none()
        
        if not pt:
            pt = StationPrepTime(
                restaurant_id=current_user.restaurant_id,
                station_id=pt_in.station_id,
                item_category=pt_in.item_category,
                default_seconds=pt_in.default_seconds
            )
            db.add(pt)
        else:
            pt.default_seconds = pt_in.default_seconds
            
        result.append(pt)
        
    await db.commit()
    for item in result:
        await db.refresh(item)
    return result


# --- MENU ITEM STATION ASSIGNMENT ---

@router.put("/menu-items/{item_id}/station", response_model=schemas.MenuItemRead)
async def assign_station_to_item(
    item_id: UUID,
    assignment: schemas.AssignStationRequest,
    current_user: Staff = Depends(check_role(["owner", "manager"])),
    db: AsyncSession = Depends(get_db)
):
    """Assign a kitchen station to a specific menu item."""
    item = await db.get(MenuItem, item_id)
    if not item or item.restaurant_id != current_user.restaurant_id:
        raise HTTPException(status_code=404, detail="Menu item not found")

    if assignment.station_id:
        station = await db.get(KitchenStation, assignment.station_id)
        if not station or station.restaurant_id != current_user.restaurant_id:
            raise HTTPException(status_code=400, detail="Invalid kitchen station")

    item.station_id = assignment.station_id
    await db.commit()
    await db.refresh(item)
    return item


@router.post("/menu-items/bulk-assign-station")
async def bulk_assign_station(
    assignment: schemas.BulkAssignRequest,
    current_user: Staff = Depends(check_role(["owner", "manager"])),
    db: AsyncSession = Depends(get_db)
):
    """Assign a kitchen station to multiple menu items in bulk."""
    if assignment.station_id:
        station = await db.get(KitchenStation, assignment.station_id)
        if not station or station.restaurant_id != current_user.restaurant_id:
            raise HTTPException(status_code=400, detail="Invalid kitchen station")

    # Update menu items that belong to the current restaurant
    stmt = (
        update(MenuItem)
        .where(
            MenuItem.id.in_(assignment.item_ids),
            MenuItem.restaurant_id == current_user.restaurant_id
        )
        .values(station_id=assignment.station_id)
    )
    result = await db.execute(stmt)
    await db.commit()

    return {"message": f"Successfully updated {result.rowcount} menu items"}


# --- PERFORMANCE METRICS ---

@router.get("/performance", response_model=schemas.KitchenPerformanceMetrics)
async def get_performance_metrics(
    current_user: Staff = Depends(check_role(["owner", "manager", "chef"])),
    db: AsyncSession = Depends(get_db)
):
    """Get kitchen performance metrics (cached or calculated on-the-fly)."""
    # Try reading from cache (stored in RestaurantSetting)
    stmt_cache = select(RestaurantSetting).where(
        RestaurantSetting.restaurant_id == current_user.restaurant_id,
        RestaurantSetting.key == "kitchen_performance_metrics"
    )
    res_cache = await db.execute(stmt_cache)
    cache_setting = res_cache.scalar_one_or_none()
    
    if cache_setting:
        val = cache_setting.value
        # Check if the cache is older than 5 minutes
        updated_at_str = val.get("updated_at")
        if updated_at_str:
            try:
                updated_at = datetime.fromisoformat(updated_at_str)
                if datetime.utcnow() - updated_at < timedelta(minutes=5):
                    return val.get("metrics")
            except ValueError:
                pass

    # Fallback to computing on-the-fly
    now = datetime.utcnow()
    last_24h = now - timedelta(hours=24)
    
    # 1. Total order items in last 24h
    stmt_items = select(OrderItem).join(Order).where(
        Order.restaurant_id == current_user.restaurant_id,
        Order.created_at >= last_24h
    )
    res_items = await db.execute(stmt_items)
    items = res_items.scalars().all()
    
    total_items = len(items)
    
    # 2. Avg prep time in seconds
    prep_times = []
    late_count = 0
    
    # Get prep times override for mapping fallback
    stmt_pt = select(StationPrepTime).where(StationPrepTime.restaurant_id == current_user.restaurant_id)
    res_pt = await db.execute(stmt_pt)
    prep_time_overrides = res_pt.scalars().all()
    
    override_map = {(pt.station_id, pt.item_category): pt.default_seconds for pt in prep_time_overrides}

    for item in items:
        if item.started_at and item.ready_at:
            actual_seconds = (item.ready_at - item.started_at).total_seconds()
            prep_times.append(actual_seconds)
            
            # Check if it was late
            # Determine expected prep time:
            # First, check menu_item.preparation_time (minutes)
            menu_item = item.menu_item
            expected_seconds = 600
            if menu_item:
                if menu_item.preparation_time:
                    expected_seconds = menu_item.preparation_time * 60
                else:
                    # Fallback to station prep times
                    category_name = getattr(menu_item.category, 'name', '').lower()
                    cat = 'main'
                    if 'appetizer' in category_name or 'starter' in category_name:
                        cat = 'appetizer'
                    elif 'dessert' in category_name or 'sweet' in category_name:
                        cat = 'dessert'
                    elif 'beverage' in category_name or 'drink' in category_name:
                        cat = 'beverage'
                    
                    expected_seconds = override_map.get((menu_item.station_id, cat), 600)
            
            if actual_seconds > expected_seconds:
                late_count += 1
                
    avg_prep = sum(prep_times) / len(prep_times) if prep_times else 0.0
    
    # 3. Orders per hour
    stmt_orders = select(func.count(Order.id)).where(
        Order.restaurant_id == current_user.restaurant_id,
        Order.created_at >= last_24h,
        Order.status.in_([OrderStatus.ready, OrderStatus.served, OrderStatus.completed])
    )
    res_orders = await db.execute(stmt_orders)
    completed_orders_count = res_orders.scalar() or 0
    orders_per_hr = completed_orders_count / 24.0
    
    metrics = {
        "avg_prep_time_seconds": round(avg_prep, 2),
        "orders_per_hour": round(orders_per_hr, 2),
        "late_orders_count": late_count,
        "total_orders_count": total_items
    }
    
    # Update cache
    if not cache_setting:
        cache_setting = RestaurantSetting(
            restaurant_id=current_user.restaurant_id,
            key="kitchen_performance_metrics",
            value={"metrics": metrics, "updated_at": now.isoformat()}
        )
        db.add(cache_setting)
    else:
        cache_setting.value = {"metrics": metrics, "updated_at": now.isoformat()}
        
    await db.commit()
    return metrics
