# tests/test_kitchen_system.py
import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException
from app.api.v1.endpoints.kitchen_admin import create_station
from app.api.v1.endpoints.kitchen import start_item, ready_item
from app.schemas import schemas
from app.models import KitchenStation, MenuItem, OrderItem, Order, OrderStatus
from app.services.kitchen_routing import KitchenRoutingService


@pytest.mark.asyncio
async def test_station_creation():
    """
    Test creating a kitchen station.
    """
    db = AsyncMock()
    db.add = MagicMock()
    current_user = MagicMock()
    current_user.restaurant_id = uuid4()
    
    station_data = schemas.KitchenStationCreate(
        name="Hot Line",
        display_name="Grill & Sauté",
        station_type="hot",
        display_order=1,
        is_active=True
    )
    
    res = await create_station(station_in=station_data, current_user=current_user, db=db)
    
    assert res.name == "Hot Line"
    assert res.display_name == "Grill & Sauté"
    assert res.station_type == "hot"
    assert res.display_order == 1
    assert res.is_active is True
    # Verify that display settings and default prep times are added
    assert db.add.call_count > 1
    db.commit.assert_called()


@pytest.mark.asyncio
async def test_direct_menu_item_routing():
    """
    Test direct menu item station assignment lookup.
    """
    db = AsyncMock()
    restaurant_id = uuid4()
    menu_item_id = uuid4()
    station_id = uuid4()
    
    # 1. Test when item has a station assigned
    res_menu = MagicMock()
    res_menu.scalar_one_or_none.return_value = station_id
    
    db.execute.return_value = res_menu
    
    routing_service = KitchenRoutingService(db)
    resolved_station_id = await routing_service.get_station_for_item(menu_item_id, restaurant_id)
    assert resolved_station_id == station_id
    
    # 2. Test fallback when item has no station assigned (look up Main Kitchen)
    db.execute.side_effect = None
    
    res_menu_none = MagicMock()
    res_menu_none.scalar_one_or_none.return_value = None
    
    main_kitchen_id = uuid4()
    res_main = MagicMock()
    res_main.scalar_one_or_none.return_value = main_kitchen_id
    
    db.execute.side_effect = [res_menu_none, res_main]
    
    resolved_station_id = await routing_service.get_station_for_item(menu_item_id, restaurant_id)
    assert resolved_station_id == main_kitchen_id


@pytest.mark.asyncio
async def test_prep_time_sequencing():
    """
    Test calculating optimal preparation sequencing delays based on prep times.
    """
    db = AsyncMock()
    routing_service = KitchenRoutingService(db)
    
    items = [
        {"name": "Burger", "prep_time_seconds": 600}, # 10 mins
        {"name": "Fries", "prep_time_seconds": 300},  # 5 mins
        {"name": "Steak", "prep_time_seconds": 900}   # 15 mins
    ]
    
    sequenced = routing_service.calculate_prep_sequence(items)
    
    # Maximum prep time is 900 seconds (Steak).
    # Steak start delay: 900 - 900 = 0
    # Burger start delay: 900 - 600 = 300
    # Fries start delay: 900 - 300 = 600
    
    assert sequenced[2]['start_delay'] == 0
    assert sequenced[0]['start_delay'] == 300
    assert sequenced[1]['start_delay'] == 600


@pytest.mark.asyncio
async def test_item_start_ready_flow():
    """
    Test marking an individual order item as preparing, then ready,
    and verifying order status transitions.
    """
    db = AsyncMock()
    restaurant_id = uuid4()
    order_id = uuid4()
    item_id = uuid4()
    
    current_user = MagicMock()
    current_user.restaurant_id = restaurant_id
    
    # Mock items and order
    order_item = OrderItem(
        id=item_id,
        order_id=order_id,
        status=OrderStatus.received,
        started_at=None,
        ready_at=None
    )
    order_item.menu_item = MenuItem(name="Burger")
    
    order = Order(
        id=order_id,
        restaurant_id=restaurant_id,
        status=OrderStatus.received
    )
    
    db.get.side_effect = lambda model, oid: order_item if model == OrderItem else order
    
    # Mock WebSocket manager broadcast using AsyncMock to be awaitable
    with patch("app.api.v1.endpoints.kitchen.manager.broadcast", new_callable=AsyncMock) as ws_broadcast_mock, \
         patch("app.api.v1.endpoints.kitchen.KitchenRoutingService.get_station_for_item", return_value=uuid4()):
        
        # 1. Start cooking the item
        res_start = await start_item(order_id=order_id, item_id=item_id, restaurant_id=restaurant_id, db=db)
        assert res_start == {"msg": "Item preparation started"}
        assert order_item.status == OrderStatus.preparing
        assert order_item.started_at is not None
        assert order.status == OrderStatus.preparing
        
        # 2. Mark the item as ready
        # Mock DB select for all items in order
        all_items_res = MagicMock()
        all_items_res.scalars.return_value.all.return_value = [order_item]
        db.execute.return_value = all_items_res
        
        res_ready = await ready_item(order_id=order_id, item_id=item_id, restaurant_id=restaurant_id, db=db)
        assert res_ready["msg"] == "Item marked ready"
        assert res_ready["order_is_ready"] is True
        assert order_item.status == OrderStatus.ready
        assert order_item.ready_at is not None
        assert order.status == OrderStatus.ready


@pytest.mark.asyncio
async def test_websocket_broadcast_to_station():
    """
    Test routing and broadcasting a new order event via websockets.
    """
    from app.websockets.manager import ConnectionManager
    manager = ConnectionManager()
    
    mock_ws_station = AsyncMock()
    mock_ws_admin = AsyncMock()
    
    # Register connections using identifiers without underscores
    restaurant_id = "restaurant1"
    station_id = "station1"
    
    # Connect to room f"{restaurant_id}_kitchen_{station_id}"
    await manager.connect(mock_ws_station, f"{restaurant_id}_kitchen_{station_id}")
    # Connect to admin room f"{restaurant_id}_admin"
    await manager.connect(mock_ws_admin, f"{restaurant_id}_admin")
    
    payload = {
        "type": "item_ready",
        "order_id": "order1",
        "item_id": "item1",
        "station_id": station_id
    }
    
    # Broadcast to station-specific room
    await manager.broadcast(payload, f"{restaurant_id}_kitchen_{station_id}")
    
    # Verify both station WS and admin WS received the message (due to admin duplication)
    mock_ws_station.send_json.assert_called_once_with(payload)
    mock_ws_admin.send_json.assert_called_once_with(payload)


@pytest.mark.asyncio
async def test_order_delayed_start_and_expediter_view():
    """
    Test calculating start delays, fetching expediter orders, and notifying stations.
    """
    from app.services.kitchen_routing import calculate_start_delays, get_order_completion_status
    from app.api.v1.endpoints.expediter import get_expediter_orders, notify_station_to_start, NotifyStationRequest
    
    # 1. Test calculate_start_delays
    items = [
        {"menu_item_id": uuid4(), "preparation_time": 900}, # 15 mins
        {"menu_item_id": uuid4(), "preparation_time": 300}  # 5 mins
    ]
    delayed = calculate_start_delays(items)
    assert delayed[0]['start_delay_seconds'] == 0
    assert delayed[1]['start_delay_seconds'] == 600
    assert delayed[0]['estimated_ready_at'] == delayed[1]['estimated_ready_at']

    # 2. Test get_order_completion_status
    db = AsyncMock()
    order_id = uuid4()
    
    order_item1 = OrderItem(id=uuid4(), order_id=order_id, status=OrderStatus.ready, estimated_ready_at=None)
    order_item2 = OrderItem(id=uuid4(), order_id=order_id, status=OrderStatus.received, estimated_ready_at=None)
    
    res_items = MagicMock()
    res_items.scalars.return_value.all.return_value = [order_item1, order_item2]
    db.execute.return_value = res_items
    
    status = await get_order_completion_status(order_id, db)
    assert status['all_ready'] is False
    assert status['ready_count'] == 1
    assert status['waiting_count'] == 1
    assert status['ready_percentage'] == 50.0

    # 3. Test get_expediter_orders endpoint
    restaurant_id = uuid4()
    order = Order(
        id=order_id,
        restaurant_id=restaurant_id,
        order_number="ORDER123",
        table_id=uuid4(),
        status=OrderStatus.received
    )
    order_item2.menu_item = MenuItem(name="Burger", station_id=uuid4())
    order_item1.menu_item = MenuItem(name="Fries", station_id=uuid4())
    order.items = [order_item1, order_item2]
    
    res_orders = MagicMock()
    res_orders.scalars.return_value.all.return_value = [order]
    
    res_stations = MagicMock()
    res_stations.scalars.return_value.all.return_value = []
    
    db.execute.side_effect = [res_orders, res_stations, res_items]
    
    res_endpoint = await get_expediter_orders(restaurant_id=restaurant_id, db=db)
    assert len(res_endpoint) == 1
    assert res_endpoint[0]['order_number'] == "ORDER123"
    assert res_endpoint[0]['all_ready'] is False
    assert res_endpoint[0]['completion']['ready_count'] == 1

    # 4. Test notify_station_to_start endpoint
    db.execute.side_effect = None
    res_notify_items = MagicMock()
    res_notify_items.scalars.return_value.all.return_value = [order_item2]
    db.execute.return_value = res_notify_items
    
    with patch("app.api.v1.endpoints.expediter.manager.broadcast", new_callable=AsyncMock) as mock_broadcast:
        res_notify = await notify_station_to_start(
            order_id=order_id,
            request=NotifyStationRequest(station_id=uuid4()),
            restaurant_id=restaurant_id,
            db=db
        )
        assert res_notify == {"success": True}
        assert order_item2.start_delay_seconds == 0
        db.commit.assert_called()
        assert mock_broadcast.call_count == 2


@pytest.mark.asyncio
async def test_hold_order_item():
    """
    Test putting an order item on hold.
    """
    from app.api.v1.endpoints.kitchen import hold_order_item
    from datetime import datetime, UTC
    
    db = AsyncMock()
    order_id = uuid4()
    item_id = uuid4()
    restaurant_id = uuid4()
    
    order_item = OrderItem(
        id=item_id,
        order_id=order_id,
        status=OrderStatus.preparing,
        is_held=False
    )
    db.get.return_value = order_item
    
    resume_time = datetime.now(UTC)
    request_data = schemas.HoldRequest(
        reason="Out of stock",
        resume_at=resume_time
    )
    
    with patch("app.api.v1.endpoints.kitchen.manager.broadcast", new_callable=AsyncMock) as mock_broadcast, \
         patch("app.api.v1.endpoints.kitchen.KitchenRoutingService.get_station_for_item", return_value=uuid4()):
        
        res = await hold_order_item(
            order_id=order_id,
            item_id=item_id,
            request=request_data,
            restaurant_id=restaurant_id,
            db=db
        )
        
        assert res == {"success": True}
        assert order_item.is_held is True
        assert order_item.hold_reason == "Out of stock"
        assert order_item.hold_resume_at == resume_time
        assert order_item.hold_started_at is not None
        db.commit.assert_called_once()
        assert mock_broadcast.call_count == 2


@pytest.mark.asyncio
async def test_resume_order_item():
    """
    Test resuming a held order item.
    """
    from app.api.v1.endpoints.kitchen import resume_order_item
    from datetime import datetime, timedelta
    
    db = AsyncMock()
    order_id = uuid4()
    item_id = uuid4()
    restaurant_id = uuid4()
    
    started_at = datetime.utcnow() - timedelta(minutes=5)
    hold_started_at = datetime.utcnow() - timedelta(minutes=2)
    
    order_item = OrderItem(
        id=item_id,
        order_id=order_id,
        status=OrderStatus.preparing,
        is_held=True,
        hold_reason="Waiting",
        hold_resume_at=datetime.utcnow() + timedelta(minutes=5),
        hold_started_at=hold_started_at,
        started_at=started_at
    )
    db.get.return_value = order_item
    
    with patch("app.api.v1.endpoints.kitchen.manager.broadcast", new_callable=AsyncMock) as mock_broadcast, \
         patch("app.api.v1.endpoints.kitchen.KitchenRoutingService.get_station_for_item", return_value=uuid4()):
        
        res = await resume_order_item(
            order_id=order_id,
            item_id=item_id,
            restaurant_id=restaurant_id,
            db=db
        )
        
        assert res == {"success": True}
        assert order_item.is_held is False
        assert order_item.hold_reason is None
        assert order_item.hold_resume_at is None
        assert order_item.hold_started_at is None
        assert order_item.started_at > started_at  # The timer should shift forward by the hold duration
        db.commit.assert_called_once()
        assert mock_broadcast.call_count == 2


@pytest.mark.asyncio
async def test_clear_order_from_kds():
    """
    Test clearing an order from KDS manually.
    """
    from app.api.v1.endpoints.kitchen import clear_order_from_kds
    
    db = AsyncMock()
    order_id = uuid4()
    restaurant_id = uuid4()
    
    order = Order(
        id=order_id,
        restaurant_id=restaurant_id,
        status=OrderStatus.ready
    )
    db.get.return_value = order
    
    with patch("app.api.v1.endpoints.kitchen.manager.broadcast", new_callable=AsyncMock) as mock_broadcast:
        res = await clear_order_from_kds(
            order_id=order_id,
            restaurant_id=restaurant_id,
            db=db
        )
        
        assert res == {"success": True}
        assert order.status == OrderStatus.completed
        assert order.completed_at is not None
        db.commit.assert_called_once()
        mock_broadcast.assert_called_once_with(
            {"type": "order.cleared", "order_id": str(order_id)},
            f"{restaurant_id}_kitchen"
        )


