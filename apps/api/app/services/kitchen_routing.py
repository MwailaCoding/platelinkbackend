# app/services/kitchen_routing.py
from typing import List, Dict, Optional, Any
from uuid import UUID
from datetime import datetime, timezone, timedelta
from sqlalchemy import select
from app.models import MenuItem, KitchenStation, OrderItem, OrderStatus
from sqlalchemy.ext.asyncio import AsyncSession

class KitchenRoutingService:
    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def get_station_for_item(self, menu_item_id: Optional[UUID], restaurant_id: UUID) -> Optional[UUID]:
        """
        Return station_id (UUID) directly from menu item:
        1. Check direct MenuItem.station_id assignment.
        2. Fallback to default station (Main Kitchen).
        """
        if menu_item_id:
            stmt = select(MenuItem.station_id).where(
                MenuItem.id == menu_item_id,
                MenuItem.restaurant_id == restaurant_id
            )
            res = await self.db.execute(stmt)
            station_id = res.scalar_one_or_none()
            if station_id:
                return station_id

        # Fallback to default station (look up 'Main Kitchen')
        stmt_default = select(KitchenStation.id).where(
            KitchenStation.restaurant_id == restaurant_id,
            KitchenStation.name.ilike("Main Kitchen"),
            KitchenStation.is_active == True
        )
        res_default = await self.db.execute(stmt_default)
        default_id = res_default.scalar_one_or_none()
        if default_id:
            return default_id

        # Fallback to the first active station
        stmt_first = select(KitchenStation.id).where(
            KitchenStation.restaurant_id == restaurant_id,
            KitchenStation.is_active == True
        ).order_by(KitchenStation.display_order.asc())
        res_first = await self.db.execute(stmt_first)
        first_id = res_first.scalar_one_or_none()
        return first_id

    async def split_order_by_station(self, order_items: List[Any], restaurant_id: UUID) -> Dict[str, List[Any]]:
        """
        Split order items by station.
        Supports both dictionaries and SQLAlchemy model instances.
        Returns a dictionary mapping station_id (str) to lists of items.
        """
        result = {}
        for item in order_items:
            # Extract menu_item_id depending on type
            if isinstance(item, dict):
                menu_item_id_raw = item.get('menu_item_id')
            else:
                menu_item_id_raw = getattr(item, 'menu_item_id', None)
                
            menu_item_id = UUID(str(menu_item_id_raw)) if menu_item_id_raw else None
            
            station_uuid = await self.get_station_for_item(menu_item_id, restaurant_id)
            station_id_str = str(station_uuid) if station_uuid else "default"
            
            if station_id_str not in result:
                result[station_id_str] = []
            result[station_id_str].append(item)
            
        return result

    def calculate_prep_sequence(self, items: List[dict]) -> List[dict]:
        """
        Calculate optimal start delays for prep-time sequencing.
        Accepts list of item dictionaries containing 'prep_time_seconds' or model objects.
        Injects or calculates 'start_delay' (seconds) for each item relative to the maximum prep time.
        """
        if not items:
            return []
            
        # Get prep times
        prep_times = []
        for item in items:
            if isinstance(item, dict):
                pt = item.get('prep_time_seconds') or item.get('prep_time') or 600
            else:
                # MenuItem model has preparation_time in minutes, convert to seconds
                pt = getattr(item, 'prep_time_seconds', None)
                if pt is None:
                    menu_item = getattr(item, 'menu_item', None)
                    if menu_item and getattr(menu_item, 'preparation_time', None):
                        pt = menu_item.preparation_time * 60
                    else:
                        pt = 600
            prep_times.append(pt)
            
        max_prep = max(prep_times)
        
        sequenced_items = []
        for idx, item in enumerate(items):
            delay = max_prep - prep_times[idx]
            if isinstance(item, dict):
                item_copy = item.copy()
                item_copy['start_delay'] = delay
                sequenced_items.append(item_copy)
            else:
                # For SQLAlchemy objects, we can set temporary dynamic attribute
                setattr(item, 'start_delay', delay)
                sequenced_items.append(item)
                
        return sequenced_items


def calculate_start_delays(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Calculate when each item should start cooking so everything finishes together.
    
    Example:
    - Burger (Grill): 15 min (900s) -> start now (delay 0)
    - Fries (Fry): 5 min (300s) -> start in 10 min (delay 600s)
    
    All finish at max_prep_time.
    """
    if not items:
        return items
        
    # Find the longest preparation time (the bottleneck)
    max_prep_time = max(item.get('preparation_time', 900) for item in items)
    
    now_utc = datetime.now(timezone.utc)
    for item in items:
        prep_time = item.get('preparation_time', 900)
        item['start_delay_seconds'] = max_prep_time - prep_time
        item['estimated_start_at'] = now_utc + timedelta(seconds=item['start_delay_seconds'])
        item['estimated_ready_at'] = now_utc + timedelta(seconds=max_prep_time)
        
    return items


async def get_order_completion_status(order_id: UUID, db: AsyncSession) -> Dict[str, Any]:
    """
    Check if all items in an order are ready.
    """
    stmt = select(OrderItem).where(OrderItem.order_id == order_id)
    res = await db.execute(stmt)
    order_items = res.scalars().all()
    
    ready_items = []
    waiting_items = []
    
    for item in order_items:
        if item.status == OrderStatus.ready:
            ready_items.append(item)
        else:
            waiting_items.append(item)
            
    all_ready = len(waiting_items) == 0
    
    max_ready = None
    for item in order_items:
        if item.estimated_ready_at:
            ready_time = item.estimated_ready_at
            if max_ready is None or ready_time > max_ready:
                max_ready = ready_time
                
    total_count = len(order_items)
    ready_count = len(ready_items)
    waiting_count = len(waiting_items)
    
    return {
        'all_ready': all_ready,
        'ready_count': ready_count,
        'waiting_count': waiting_count,
        'estimated_ready_at': max_ready,
        'ready_percentage': (ready_count / total_count) * 100 if total_count > 0 else 0
    }

