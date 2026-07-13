# app/tasks/kitchen_tasks.py
from datetime import datetime, timedelta
import asyncio
from app.core.celery_app import celery_app
from app.db.session import async_session_local
from app.models import RestaurantSetting, Order, OrderItem, OrderStatus
from sqlalchemy import select
from app.websockets.connection_manager import manager as ws_manager
import logging

logger = logging.getLogger("platelink")

@celery_app.task
def auto_clear_ready_orders():
    """
    Automatically clear orders that have been ready for too long.
    Runs every minute.
    """
    async def _clear():
        async with async_session_local() as db:
            # Get settings where key is 'auto_clear_ready_minutes'
            stmt = select(RestaurantSetting).where(
                RestaurantSetting.key == 'auto_clear_ready_minutes'
            )
            result = await db.execute(stmt)
            settings = result.scalars().all()
            
            for setting in settings:
                try:
                    minutes = int(setting.value)
                except (ValueError, TypeError):
                    continue
                
                if minutes <= 0:
                    continue
                
                cutoff = datetime.utcnow() - timedelta(minutes=minutes)
                
                # Find orders that are ready for this restaurant
                stmt_orders = select(Order).where(
                    Order.restaurant_id == setting.restaurant_id,
                    Order.status == OrderStatus.ready
                )
                res_orders = await db.execute(stmt_orders)
                orders = res_orders.scalars().all()
                
                for order in orders:
                    items = order.items
                    if not items:
                        continue
                    
                    # Check if all items are ready, and find the latest ready time
                    if all(i.status == OrderStatus.ready for i in items):
                        ready_times = [i.ready_at for i in items if i.ready_at]
                        if ready_times:
                            latest_ready = max(ready_times)
                            # Strip timezone if latest_ready is timezone-aware to match cutoff (naive UTC)
                            latest_ready_naive = latest_ready.replace(tzinfo=None) if latest_ready.tzinfo else latest_ready
                            
                            if latest_ready_naive < cutoff:
                                order.status = OrderStatus.completed
                                order.completed_at = datetime.utcnow()
                                
                                # Broadcast to kitchen and waiter screens
                                payload = {
                                    "type": "order.auto_cleared",
                                    "order_id": str(order.id)
                                }
                                await ws_manager.broadcast(payload, f"{order.restaurant_id}_kitchen")
                                await ws_manager.broadcast(payload, f"{order.restaurant_id}_waiter")
                                logger.info(f"Auto-cleared order {order.id} for restaurant {order.restaurant_id}")
            
            await db.commit()

    try:
        # Run the async clearing task in a synchronous context
        asyncio.run(_clear())
    except Exception as e:
        logger.error(f"Error in auto_clear_ready_orders: {e}")
