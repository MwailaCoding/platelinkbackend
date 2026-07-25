# app/websockets/manager.py
from typing import List, Dict
from fastapi import WebSocket
import logging

logger = logging.getLogger("platelink.websockets")

class ConnectionManager:
    def __init__(self):
        # room_id -> list of websockets
        self.active_connections: Dict[str, List[WebSocket]] = {}
        # session_token -> websocket (retaining compatibility if needed)
        self.session_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, room_id: str):
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
        self.active_connections[room_id].append(websocket)
        logger.info(f"WebSocket client connected to room: {room_id}")

    def disconnect(self, websocket: WebSocket, room_id: str):
        if room_id in self.active_connections:
            try:
                self.active_connections[room_id].remove(websocket)
            except ValueError:
                pass
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]
        logger.info(f"WebSocket client disconnected from room: {room_id}")

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        await websocket.send_json(message)

    async def broadcast(self, message: dict, room_id: str):
        """
        Broadcast a message to a specific room, with smart fallback and routing:
        1. If room_id has no suffix (e.g. raw restaurant_id), send it to admin, kitchen, and waiter channels.
        2. If room_id is specific (e.g. restaurant_id_kitchen or restaurant_id_waiter), send it to that channel AND duplicate to restaurant_id_admin.
        """
        target_rooms = [room_id]

        if "_" not in room_id:
            # Broadcast to all roles of this restaurant
            target_rooms = [
                f"{room_id}_admin",
                f"{room_id}_kitchen",
                f"{room_id}_waiter",
                f"{room_id}_waiters",
                room_id
            ]
        else:
            # Specific role room, duplicate to admin
            parts = room_id.split("_")
            if len(parts) >= 2:
                restaurant_id = parts[0]
                admin_room = f"{restaurant_id}_admin"
                if admin_room not in target_rooms:
                    target_rooms.append(admin_room)

        # Normalize message event keys for frontend compat if necessary
        # Frontend admin-dashboard expects data.type to be:
        # - 'order.new' or 'order_new'
        # - 'order.status_updated' or 'order_status'
        # Let's ensure types are mapped correctly
        event_type = message.get("type")
        normalized_message = message.copy()
        if event_type == "new_order":
            normalized_message["type"] = "order.new"
        elif event_type == "order_status":
            normalized_message["type"] = "order.status_updated"

        # Broadcast to all determined target rooms
        for r_id in target_rooms:
            if r_id in self.active_connections:
                for connection in list(self.active_connections[r_id]):
                    try:
                        await connection.send_json(normalized_message)
                    except Exception as e:
                        logger.warning(f"Failed to send websocket message in room {r_id}: {e}")
                        try:
                            self.active_connections[r_id].remove(connection)
                        except ValueError:
                            pass

    async def broadcast_to_kitchen(self, restaurant_id: str, message: dict):
        await self.broadcast(message, f"{restaurant_id}_kitchen")

    async def broadcast_to_waiter(self, restaurant_id: str, message: dict):
        await self.broadcast(message, f"{restaurant_id}_waiter")

    async def broadcast_order_to_station(self, order: dict, station_id: str):
        """Send order only to the specific station screen"""
        room = f"kitchen_{station_id}"
        await self.broadcast({
            "type": "order.new",
            "payload": order
        }, room)

    async def broadcast_to_all_stations(self, event: dict, station_ids: List[str]):
        """Send event to multiple stations"""
        for station_id in station_ids:
            await self.broadcast(event, f"kitchen_{station_id}")

manager = ConnectionManager()
