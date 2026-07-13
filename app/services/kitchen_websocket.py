# app/services/kitchen_websocket.py
from app.websockets.manager import manager

async def broadcast_new_order_to_station(order: dict, restaurant_id: str):
    """
    Broadcast new order only to the station that needs it.
    If no station_id is defined on the order, it falls back to the generic kitchen channel.
    """
    station_id = order.get('station_id')
    station_suffix = f"_{station_id}" if station_id else ""
    
    # Broadcast to specific station room (which also duplicates to admin room)
    await manager.broadcast(
        {
            "type": "order.new",
            "payload": order
        },
        f"{restaurant_id}_kitchen{station_suffix}"
    )
