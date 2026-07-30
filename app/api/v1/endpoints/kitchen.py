# app/api/v1/endpoints/kitchen.py
from typing import List, Optional
from datetime import datetime, timedelta
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Body, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, update
from sqlalchemy.orm import selectinload
from app.core.deps import get_db
from app.models import (
    Order, OrderItem, OrderStatus, MenuItem, KitchenDisplaySetting,
    KitchenStation, Restaurant
)
from app.websockets.manager import manager
from app.schemas import schemas
from app.services.kitchen_routing import KitchenRoutingService

router = APIRouter()


def format_order_for_kitchen(order: Order) -> dict:
    table_num = None
    if getattr(order, "table", None) and getattr(order.table, "table_number", None) is not None:
        table_num = order.table.table_number
    elif getattr(order, "table_number", None) is not None:
        table_num = order.table_number

    formatted_items = []
    for item in (order.items or []):
        item_name = "Dish"
        if getattr(item, "menu_item", None) and getattr(item.menu_item, "name", None):
            item_name = item.menu_item.name
        elif getattr(item, "name", None):
            item_name = item.name

        formatted_items.append({
            "id": str(item.id),
            "name": item_name,
            "quantity": item.quantity,
            "status": item.status.value if hasattr(item.status, "value") else str(item.status),
            "special_instructions": getattr(item, "special_instructions", None),
            "estimated_start_at": item.estimated_start_at.isoformat() if getattr(item, "estimated_start_at", None) else None,
            "estimated_ready_at": item.estimated_ready_at.isoformat() if getattr(item, "estimated_ready_at", None) else None,
            "start_delay_seconds": getattr(item, "start_delay_seconds", 0),
            "is_held": getattr(item, "is_held", False),
            "hold_reason": getattr(item, "hold_reason", None),
            "hold_resume_at": item.hold_resume_at.isoformat() if getattr(item, "hold_resume_at", None) else None,
            "station_id": str(getattr(item, "station_id", "")) if getattr(item, "station_id", None) else None,
        })

    return {
        "id": str(order.id),
        "order_number": order.order_number or str(order.id)[:8].upper(),
        "table_number": table_num,
        "order_type": "table" if table_num is not None else "takeaway",
        "created_at": order.created_at.isoformat() if order.created_at else datetime.utcnow().isoformat(),
        "started_at": order.started_at.isoformat() if getattr(order, "started_at", None) else None,
        "status": order.status.value if hasattr(order.status, "value") else str(order.status),
        "items": formatted_items,
        "preparation_time": getattr(order, "preparation_time", 15),
        "waiter_notes": getattr(order, "notes", None) or getattr(order, "waiter_notes", None),
    }

async def filter_orders_by_station(
    orders: List[Order],
    station_id: Optional[UUID],
    restaurant_id: UUID,
    db: AsyncSession
) -> List[dict]:
    """
    Helper function to filter orders and their items by kitchen station.
    """
    routing_service = KitchenRoutingService(db)
    
    # Always resolve and populate station_id for all items
    for order in orders:
        for item in order.items:
            item.station_id = await routing_service.get_station_for_item(item.menu_item_id, restaurant_id)

    formatted_orders = []

    for order in orders:
        station_items = []
        for item in order.items:
            # Respect pacing: only show items that have been fired
            if getattr(item, 'is_fired', True) == False:
                continue
                
            if not station_id or str(item.station_id) == str(station_id):
                station_items.append(item)
        
        if station_items:
            order.items = station_items
            formatted_orders.append(format_order_for_kitchen(order))

    return formatted_orders


@router.get("/restaurants")
async def list_active_restaurants(
    db: AsyncSession = Depends(get_db)
):
    """List all active restaurants for initial setup."""
    stmt = select(Restaurant).where(
        Restaurant.is_active == True,
        Restaurant.deleted_at == None
    )
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/stations")
async def list_stations_public(
    restaurant_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """List all kitchen stations for the restaurant (public endpoint)."""
    stmt = select(KitchenStation).where(
        KitchenStation.restaurant_id == restaurant_id
    ).order_by(KitchenStation.display_order.asc())
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/orders/new")
async def get_new_orders(
    restaurant_id: UUID = Query(...),
    station_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Orders waiting to be accepted by kitchen, filtered by station.
    """
    stmt = select(Order).options(
        selectinload(Order.table),
        selectinload(Order.items).selectinload(OrderItem.menu_item)
    ).where(
        Order.restaurant_id == restaurant_id,
        Order.status == OrderStatus.received
    ).order_by(Order.created_at.asc())
    result = await db.execute(stmt)
    orders = result.scalars().all()
    
    return await filter_orders_by_station(orders, station_id, restaurant_id, db)


@router.get("/orders/in-progress")
async def get_in_progress_orders(
    restaurant_id: UUID = Query(...),
    station_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Orders in progress (cooking) in the kitchen, filtered by station.
    """
    stmt = select(Order).options(
        selectinload(Order.table),
        selectinload(Order.items).selectinload(OrderItem.menu_item)
    ).where(
        Order.restaurant_id == restaurant_id,
        Order.status == OrderStatus.preparing
    ).order_by(Order.created_at.asc())
    result = await db.execute(stmt)
    orders = result.scalars().all()
    
    return await filter_orders_by_station(orders, station_id, restaurant_id, db)


@router.get("/orders/ready")
async def get_ready_orders(
    restaurant_id: UUID = Query(...),
    station_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Orders marked as ready (cooked/dispatching) in the kitchen, filtered by station.
    """
    stmt = select(Order).options(
        selectinload(Order.table),
        selectinload(Order.items).selectinload(OrderItem.menu_item)
    ).where(
        Order.restaurant_id == restaurant_id,
        Order.status == OrderStatus.ready
    ).order_by(Order.created_at.desc())
    result = await db.execute(stmt)
    orders = result.scalars().all()
    
    return await filter_orders_by_station(orders, station_id, restaurant_id, db)


@router.put("/orders/{order_id}/accept")
async def accept_order(
    order_id: UUID,
    restaurant_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Kitchen accepts the order (no staff tracking).
    """
    order = await db.get(Order, order_id)
    if not order or order.restaurant_id != restaurant_id:
        raise HTTPException(status_code=404, detail="Order not found")
        
    order.status = OrderStatus.preparing
    await db.commit()
    
    est_ready = order.estimated_ready_at.isoformat() if order.estimated_ready_at else None

    # Broadcast to customer session
    await manager.broadcast(
        {"type": "kitchen_accepted", "order_id": str(order_id), "estimated_ready_at": est_ready},
        f"session_{order.session_id}"
    )
    # Broadcast to kitchen and waiters
    await manager.broadcast(
        {"type": "order.status_updated", "order_id": str(order_id), "status": "preparing", "estimated_ready_at": est_ready},
        str(restaurant_id)
    )
    await manager.broadcast(
        {"type": "order.status_updated", "order_id": str(order_id), "status": "preparing", "estimated_ready_at": est_ready},
        f"session_{order.session_id}"
    )
    return {"msg": "Order accepted"}


@router.put("/orders/{order_id}/items/{item_id}/start")
async def start_item(
    order_id: UUID,
    item_id: UUID,
    restaurant_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Mark an individual order item as started.
    """
    item = await db.get(OrderItem, item_id)
    if not item or item.order_id != order_id:
        raise HTTPException(status_code=404, detail="Item not found in this order")
        
    item.status = OrderStatus.preparing
    item.started_at = datetime.utcnow()
    
    # Auto-start order if it was received
    order = await db.get(Order, order_id)
    if order and order.status == OrderStatus.received:
        order.status = OrderStatus.preparing
        
    await db.commit()
    
    # Determine item station to broadcast to correct station
    routing_service = KitchenRoutingService(db)
    station_id = await routing_service.get_station_for_item(item.menu_item_id, restaurant_id)
    station_suffix = f"_{station_id}" if station_id else ""
    
    payload = {
        "type": "item_started",
        "order_id": str(order_id),
        "item_id": str(item_id),
        "station_id": str(station_id) if station_id else None
    }
    
    # Broadcast to station-specific kitchen room and generic kitchen room
    await manager.broadcast(payload, f"{restaurant_id}_kitchen{station_suffix}")
    await manager.broadcast(payload, f"{restaurant_id}_kitchen")
    
    return {"msg": "Item preparation started"}


@router.put("/orders/{order_id}/items/{item_id}/ready")
async def ready_item(
    order_id: UUID,
    item_id: UUID,
    restaurant_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Mark an individual order item as ready.
    Check if all items in order are ready, and if so, mark order as ready.
    """
    item = await db.get(OrderItem, item_id)
    if not item or item.order_id != order_id:
        raise HTTPException(status_code=404, detail="Item not found in this order")
        
    item.status = OrderStatus.ready
    item.ready_at = datetime.utcnow()
    
    # Check if all items in order are ready
    order = await db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    stmt = select(OrderItem).where(OrderItem.order_id == order_id)
    res = await db.execute(stmt)
    all_items = res.scalars().all()
    
    order_is_ready = all(i.status == OrderStatus.ready for i in all_items)
    if order_is_ready:
        order.status = OrderStatus.ready
        
    await db.commit()
    
    # Determine item station to broadcast
    routing_service = KitchenRoutingService(db)
    station_id = await routing_service.get_station_for_item(item.menu_item_id, restaurant_id)
    station_suffix = f"_{station_id}" if station_id else ""
    
    payload = {
        "type": "item_ready",
        "order_id": str(order_id),
        "item_id": str(item_id),
        "station_id": str(station_id) if station_id else None,
        "order_is_ready": order_is_ready,
        "table_number": order.table_number
    }
    
    # Broadcast to station-specific room, generic kitchen room, waiters, and customer session
    await manager.broadcast(payload, f"{restaurant_id}_kitchen{station_suffix}")
    await manager.broadcast(payload, f"{restaurant_id}_kitchen")
    await manager.broadcast(payload, f"{restaurant_id}_waiters")
    await manager.broadcast(payload, f"{restaurant_id}_waiter")
    if order.session_id:
        await manager.broadcast(payload, f"session_{order.session_id}")
        if order_is_ready:
            await manager.broadcast(
                {"type": "order.status_updated", "order_id": str(order_id), "status": "ready"},
                f"session_{order.session_id}"
            )
    
    return {"msg": "Item marked ready", "order_is_ready": order_is_ready}


@router.put("/orders/{order_id}/complete")
async def complete_order(
    order_id: UUID,
    restaurant_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Mark order as completed (picked up by waiter, status to 'completed').
    """
    order = await db.get(Order, order_id)
    if not order or order.restaurant_id != restaurant_id:
        raise HTTPException(status_code=404, detail="Order not found")
        
    order.status = OrderStatus.completed
    await db.commit()
    
    payload = {
        "type": "order_completed",
        "order_id": str(order_id)
    }
    await manager.broadcast(payload, f"{restaurant_id}_kitchen")
    await manager.broadcast(payload, f"{restaurant_id}_waiter")
    if order.session_id:
        await manager.broadcast(payload, f"session_{order.session_id}")
        await manager.broadcast(
            {"type": "order.status_updated", "order_id": str(order_id), "status": "completed"},
            f"session_{order.session_id}"
        )
    return {"msg": "Order completed"}


@router.post("/items/{item_id}/sold-out")
async def mark_sold_out(
    item_id: UUID,
    restaurant_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Kitchen marks an item as sold out.
    """
    item = await db.get(MenuItem, item_id)
    if not item or item.restaurant_id != restaurant_id:
        raise HTTPException(status_code=404, detail="Item not found")
        
    item.is_available = False
    item.stock_quantity = 0
    await db.commit()
    
    # Broadcast to all clients in restaurant
    await manager.broadcast(
        {"type": "item_sold_out", "item_id": str(item_id)},
        str(restaurant_id)
    )
    return {"msg": "Item marked as sold out"}


# --- KDS STATION SETTINGS ---

@router.get("/settings")
async def get_kds_settings(
    restaurant_id: UUID = Query(...),
    station_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Get display settings for current/specified station.
    """
    target_station_id = station_id
    if not target_station_id:
        # Fallback: get first station
        stmt_first = select(KitchenStation.id).where(
            KitchenStation.restaurant_id == restaurant_id
        ).order_by(KitchenStation.display_order.asc())
        res_first = await db.execute(stmt_first)
        target_station_id = res_first.scalar_one_or_none()
        
    if not target_station_id:
        return {
            "sound_alerts_enabled": True,
            "new_order_volume": 70,
            "ready_order_volume": 80,
            "theme": "dark",
            "font_size": "large",
            "show_timer": True,
            "show_modifiers": True,
            "auto_accept": False,
            "prep_time_buffer_percent": 10
        }
        
    stmt = select(KitchenDisplaySetting).where(
        KitchenDisplaySetting.restaurant_id == restaurant_id,
        KitchenDisplaySetting.station_id == target_station_id
    )
    res = await db.execute(stmt)
    settings = res.scalar_one_or_none()
    
    if not settings:
        # Create default settings
        settings = KitchenDisplaySetting(
            restaurant_id=restaurant_id,
            station_id=target_station_id
        )
        db.add(settings)
        await db.commit()
        await db.refresh(settings)
        
    return settings


@router.put("/settings")
async def update_kds_settings(
    restaurant_id: UUID = Query(...),
    settings_data: dict = Body(...),
    station_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Update display settings for current/specified station.
    """
    target_station_id = station_id
    if not target_station_id:
        # Fallback: get first station
        stmt_first = select(KitchenStation.id).where(
            KitchenStation.restaurant_id == restaurant_id
        ).order_by(KitchenStation.display_order.asc())
        res_first = await db.execute(stmt_first)
        target_station_id = res_first.scalar_one_or_none()
        
    if not target_station_id:
        raise HTTPException(status_code=404, detail="No kitchen station found to assign settings to.")
        
    stmt = select(KitchenDisplaySetting).where(
        KitchenDisplaySetting.restaurant_id == restaurant_id,
        KitchenDisplaySetting.station_id == target_station_id
    )
    res = await db.execute(stmt)
    settings = res.scalar_one_or_none()
    
    if not settings:
        settings = KitchenDisplaySetting(
            restaurant_id=restaurant_id,
            station_id=target_station_id
        )
        db.add(settings)
        
    for k, v in settings_data.items():
        if hasattr(settings, k):
            setattr(settings, k, v)
            
    await db.commit()
    await db.refresh(settings)
    return settings


@router.put("/orders/{order_id}/items/{item_id}/hold")
async def hold_order_item(
    order_id: UUID,
    item_id: UUID,
    request: schemas.HoldRequest,
    restaurant_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Temporarily suspend an order item (e.g., waiting for ingredient).
    Timer stops, item moves to HOLD column.
    """
    item = await db.get(OrderItem, item_id)
    if not item or item.order_id != order_id:
        raise HTTPException(status_code=404, detail="Item not found in this order")
    
    item.is_held = True
    item.hold_reason = request.reason
    item.hold_resume_at = request.resume_at
    item.hold_started_at = datetime.utcnow()
    
    await db.commit()
    
    # Broadcast to all kitchen screens
    routing_service = KitchenRoutingService(db)
    station_id = await routing_service.get_station_for_item(item.menu_item_id, restaurant_id)
    station_suffix = f"_{station_id}" if station_id else ""
    
    payload = {
        "type": "item.held",
        "order_id": str(order_id),
        "item_id": str(item_id),
        "reason": request.reason,
        "resume_at": request.resume_at.isoformat() if request.resume_at else None,
        "station_id": str(station_id) if station_id else None
    }
    
    await manager.broadcast(payload, f"{restaurant_id}_kitchen{station_suffix}")
    await manager.broadcast(payload, f"{restaurant_id}_kitchen")
    
    return {"success": True}


@router.put("/orders/{order_id}/items/{item_id}/resume")
async def resume_order_item(
    order_id: UUID,
    item_id: UUID,
    restaurant_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Resume a held order item. Timer restarts.
    """
    item = await db.get(OrderItem, item_id)
    if not item or item.order_id != order_id:
        raise HTTPException(status_code=404, detail="Item not found in this order")
    
    item.is_held = False
    item.hold_reason = None
    item.hold_resume_at = None
    
    # Adjust timer based on hold duration
    if item.hold_started_at:
        hold_duration = (datetime.utcnow() - item.hold_started_at.replace(tzinfo=None)).total_seconds()
        if item.started_at:
            item.started_at += timedelta(seconds=hold_duration)
        item.hold_started_at = None
        
    await db.commit()
    
    # Broadcast to all kitchen screens
    routing_service = KitchenRoutingService(db)
    station_id = await routing_service.get_station_for_item(item.menu_item_id, restaurant_id)
    station_suffix = f"_{station_id}" if station_id else ""
    
    payload = {
        "type": "item.resumed",
        "order_id": str(order_id),
        "item_id": str(item_id),
        "station_id": str(station_id) if station_id else None
    }
    
    await manager.broadcast(payload, f"{restaurant_id}_kitchen{station_suffix}")
    await manager.broadcast(payload, f"{restaurant_id}_kitchen")
    
    return {"success": True}


@router.post("/orders/{order_id}/clear")
async def clear_order_from_kds(
    order_id: UUID,
    restaurant_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Manually remove order from KDS screen (mark status as completed so it is cleared).
    """
    order = await db.get(Order, order_id)
    if not order or order.restaurant_id != restaurant_id:
        raise HTTPException(status_code=404, detail="Order not found")
        
    order.status = OrderStatus.completed
    order.completed_at = datetime.utcnow()
    await db.commit()
    
    await manager.broadcast(
        {"type": "order.cleared", "order_id": str(order_id)},
        f"{restaurant_id}_kitchen"
    )
    
    return {"success": True}

