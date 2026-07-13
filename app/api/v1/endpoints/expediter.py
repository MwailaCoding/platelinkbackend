# app/api/v1/endpoints/expediter.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from pydantic import BaseModel
from typing import List, Dict, Any
from datetime import datetime, timezone, timedelta

from app.core.deps import get_db
from app.models import Order, OrderItem, OrderStatus, KitchenStation
from app.services.kitchen_routing import get_order_completion_status
from app.websockets.manager import manager

router = APIRouter()

class NotifyStationRequest(BaseModel):
    station_id: UUID

@router.get("/orders")
async def get_expediter_orders(
    restaurant_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all active orders with completion status for expediter view.
    """
    stmt = select(Order).where(
        Order.restaurant_id == restaurant_id,
        Order.status.in_([OrderStatus.received, OrderStatus.preparing, OrderStatus.ready])
    ).order_by(Order.created_at.asc())
    
    res = await db.execute(stmt)
    orders = res.scalars().all()
    
    # Fetch all stations to map station_id to name
    stations_stmt = select(KitchenStation).where(KitchenStation.restaurant_id == restaurant_id)
    stations_res = await db.execute(stations_stmt)
    stations_list = stations_res.scalars().all()
    stations_map = {s.id: s.name for s in stations_list}
    
    result = []
    for order in orders:
        stations_status = {}
        for item in order.items:
            station_id_raw = item.menu_item.station_id if item.menu_item else None
            station_name = stations_map.get(station_id_raw, 'Main Kitchen') if station_id_raw else 'Main Kitchen'
            
            if station_name not in stations_status:
                stations_status[station_name] = {
                    'station_id': str(station_id_raw) if station_id_raw else '',
                    'ready': 0,
                    'total': 0,
                    'items': []
                }
            
            stations_status[station_name]['total'] += 1
            stations_status[station_name]['items'].append({
                'id': str(item.id),
                'name': item.name,
                'quantity': item.quantity,
                'status': item.status.value,
                'station_id': str(station_id_raw) if station_id_raw else '',
                'estimated_ready_at': item.estimated_ready_at.isoformat() if item.estimated_ready_at else None
            })
            
            if item.status == OrderStatus.ready:
                stations_status[station_name]['ready'] += 1
                
        completion = await get_order_completion_status(order.id, db)
        
        result.append({
            'id': str(order.id),
            'order_number': order.order_number,
            'table_number': order.table_number,
            'created_at': order.created_at.isoformat() if order.created_at else None,
            'status': order.status.value,
            'stations': stations_status,
            'completion': {
                'all_ready': completion['all_ready'],
                'ready_count': completion['ready_count'],
                'waiting_count': completion['waiting_count'],
                'estimated_ready_at': completion['estimated_ready_at'].isoformat() if completion['estimated_ready_at'] else None,
                'ready_percentage': completion['ready_percentage']
            },
            'all_ready': completion['all_ready'],
            'estimated_ready_at': completion['estimated_ready_at'].isoformat() if completion['estimated_ready_at'] else None
        })
        
    return result

@router.post("/orders/{order_id}/notify-station")
async def notify_station_to_start(
    order_id: UUID,
    request: NotifyStationRequest,
    restaurant_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Expediter can send notification to a specific station to start delayed items immediately.
    """
    # 1. Fetch order items for this station
    stmt = select(OrderItem).join(OrderItem.menu_item).where(
        OrderItem.order_id == order_id,
        OrderItem.menu_item.has(station_id=request.station_id),
        OrderItem.status == OrderStatus.received
    )
    res = await db.execute(stmt)
    items = res.scalars().all()
    
    # 2. Release delays
    now_utc = datetime.now(timezone.utc)
    for item in items:
        prep_time_seconds = (item.menu_item.preparation_time * 60) if (item.menu_item and item.menu_item.preparation_time) else 900
        item.estimated_start_at = now_utc
        item.estimated_ready_at = now_utc + timedelta(seconds=prep_time_seconds)
        item.start_delay_seconds = 0
        
    await db.commit()
    
    # 3. Broadcast to websocket channels
    await manager.broadcast(
        {"type": "order.ready_to_start", "order_id": str(order_id), "station_id": str(request.station_id)},
        f"{restaurant_id}_kitchen_{request.station_id}"
    )
    await manager.broadcast(
        {"type": "order.updated", "order_id": str(order_id)},
        f"{restaurant_id}_kitchen"
    )
    
    return {"success": True}
