# app/tasks/kitchen_metrics.py
import asyncio
import logging
from datetime import datetime, timedelta
from uuid import UUID
from sqlalchemy import select, func
from app.core.celery_app import celery_app
from app.db.session import async_session_local
from app.models import Order, OrderItem, MenuItem, RestaurantSetting, Restaurant, OrderStatus, StationPrepTime
from app.websockets.manager import manager as ws_manager

logger = logging.getLogger("platelink.tasks")

@celery_app.task
def update_kitchen_performance_metrics():
    """
    Celery task that runs every 5 minutes to compute and cache
    kitchen performance metrics for all active restaurants.
    """
    async def _update():
        async with async_session_local() as db:
            # Get all restaurants
            rest_stmt = select(Restaurant).where(Restaurant.is_active == True)
            restaurants = (await db.execute(rest_stmt)).scalars().all()
            
            now = datetime.utcnow()
            last_24h = now - timedelta(hours=24)
            
            for rest in restaurants:
                try:
                    # Compute metrics
                    stmt_items = select(OrderItem).join(Order).where(
                        Order.restaurant_id == rest.id,
                        Order.created_at >= last_24h
                    )
                    res_items = await db.execute(stmt_items)
                    items = res_items.scalars().all()
                    
                    total_items = len(items)
                    prep_times = []
                    late_count = 0
                    
                    stmt_pt = select(StationPrepTime).where(StationPrepTime.restaurant_id == rest.id)
                    res_pt = await db.execute(stmt_pt)
                    prep_time_overrides = res_pt.scalars().all()
                    
                    override_map = {(pt.station_id, pt.item_category): pt.default_seconds for pt in prep_time_overrides}
                    
                    for item in items:
                        if item.started_at and item.ready_at:
                            actual_seconds = (item.ready_at - item.started_at).total_seconds()
                            prep_times.append(actual_seconds)
                            
                            # Determine expected time
                            menu_item = item.menu_item
                            expected_seconds = 600
                            if menu_item:
                                if menu_item.preparation_time:
                                    expected_seconds = menu_item.preparation_time * 60
                                else:
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
                    
                    stmt_orders = select(func.count(Order.id)).where(
                        Order.restaurant_id == rest.id,
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
                    stmt_cache = select(RestaurantSetting).where(
                        RestaurantSetting.restaurant_id == rest.id,
                        RestaurantSetting.key == "kitchen_performance_metrics"
                    )
                    res_cache = await db.execute(stmt_cache)
                    cache_setting = res_cache.scalar_one_or_none()
                    
                    if not cache_setting:
                        cache_setting = RestaurantSetting(
                            restaurant_id=rest.id,
                            key="kitchen_performance_metrics",
                            value={"metrics": metrics, "updated_at": now.isoformat()}
                        )
                        db.add(cache_setting)
                    else:
                        cache_setting.value = {"metrics": metrics, "updated_at": now.isoformat()}
                        
                    logger.info(f"Updated performance metrics for restaurant {rest.name}")
                except Exception as e:
                    logger.error(f"Error updating kitchen metrics for {rest.name}: {e}")
                    
            await db.commit()
            
    asyncio.run(_update())


@celery_app.task
def send_slow_order_alert():
    """
    Checks for order items currently in progress that have exceeded
    their estimated preparation time and broadcasts an alert via WebSocket.
    """
    async def _check_slow_orders():
        async with async_session_local() as db:
            now = datetime.utcnow()
            
            # Select preparing order items
            stmt = select(OrderItem).where(
                OrderItem.status == OrderStatus.preparing,
                OrderItem.started_at != None
            )
            res = await db.execute(stmt)
            preparing_items = res.scalars().all()
            
            for item in preparing_items:
                # Retrieve order to get restaurant_id
                order = await db.get(Order, item.order_id)
                if not order:
                    continue
                    
                # Determine expected prep time
                menu_item = item.menu_item
                expected_seconds = 600
                if menu_item:
                    if menu_item.preparation_time:
                        expected_seconds = menu_item.preparation_time * 60
                    else:
                        # Fetch overrides
                        stmt_pt = select(StationPrepTime).where(
                            StationPrepTime.restaurant_id == order.restaurant_id,
                            StationPrepTime.station_id == menu_item.station_id
                        )
                        res_pt = await db.execute(stmt_pt)
                        pts = res_pt.scalars().all()
                        category_name = getattr(menu_item.category, 'name', '').lower()
                        cat = 'main'
                        if 'appetizer' in category_name or 'starter' in category_name:
                            cat = 'appetizer'
                        elif 'dessert' in category_name or 'sweet' in category_name:
                            cat = 'dessert'
                        elif 'beverage' in category_name or 'drink' in category_name:
                            cat = 'beverage'
                            
                        station_pt = next((pt.default_seconds for pt in pts if pt.item_category == cat), 600)
                        expected_seconds = station_pt
                
                # Check elapsed time
                elapsed_seconds = (now - item.started_at.replace(tzinfo=None)).total_seconds()
                
                if elapsed_seconds > expected_seconds:
                    # Send alert
                    logger.warning(f"Slow order item detected: {item.name} for Order {order.order_number} (elapsed: {elapsed_seconds}s, expected: {expected_seconds}s)")
                    
                    payload = {
                        "type": "kitchen_slow_order",
                        "order_id": str(order.id),
                        "order_number": order.order_number,
                        "item_id": str(item.id),
                        "item_name": item.name,
                        "elapsed_seconds": int(elapsed_seconds),
                        "expected_seconds": int(expected_seconds)
                    }
                    
                    # Broadcast alert to restaurant generic room and station room if applicable
                    station_id = menu_item.station_id if menu_item else None
                    station_suffix = f"_{station_id}" if station_id else ""
                    
                    await ws_manager.broadcast(payload, f"{order.restaurant_id}_kitchen{station_suffix}")
                    await ws_manager.broadcast(payload, f"{order.restaurant_id}_kitchen")
                    await ws_manager.broadcast(payload, f"{order.restaurant_id}_admin")
                    
    asyncio.run(_check_slow_orders())
