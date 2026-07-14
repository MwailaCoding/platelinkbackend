# app/api/v1/endpoints/customer.py
from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from jose import jwt
from app.core import security
from app.core.config import settings
from app.core.deps import get_db
from app.models import Restaurant, RestaurantSetting, Category, MenuItem, Table, CustomerSession, Order, OrderItem, WaiterCall, TableStatus, OrderStatus, PaymentStatus, SessionStatus, CallStatus
from app.schemas import schemas
from app.websockets.manager import manager
from app.services.mpesa import MpesaService

import logging
router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/menu/{slug}")
async def get_full_menu(slug: str, db: AsyncSession = Depends(get_db)):
    """
    Public menu for a restaurant.
    """
    import uuid
    try:
        uuid_obj = uuid.UUID(slug, version=4)
        is_uuid = True
    except ValueError:
        is_uuid = False

    if is_uuid:
        stmt = select(Restaurant).where(Restaurant.id == slug, Restaurant.is_active == True, Restaurant.deleted_at == None)
    else:
        stmt = select(Restaurant).where(Restaurant.slug == slug, Restaurant.is_active == True, Restaurant.deleted_at == None)
    res = await db.execute(stmt)
    restaurant = res.scalar_one_or_none()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
        
    # Categories
    stmt = select(Category).where(Category.restaurant_id == restaurant.id, Category.is_active == True).order_by(Category.display_order.asc())
    cats = (await db.execute(stmt)).scalars().all()
    
    # Items
    stmt = select(MenuItem).where(MenuItem.restaurant_id == restaurant.id, MenuItem.is_available == True)
    items = (await db.execute(stmt)).scalars().all()
    
    # Check if direct M-Pesa settings exist for this restaurant
    stmt_settings = select(RestaurantSetting).where(
        RestaurantSetting.restaurant_id == restaurant.id,
        RestaurantSetting.key == "consumer_key"
    )
    res_settings = await db.execute(stmt_settings)
    has_direct_mpesa = res_settings.scalar_one_or_none() is not None
    payment_track = "mpesa_direct" if has_direct_mpesa else "pesapal"
    
    return {
        "restaurant": {
            "name": restaurant.name,
            "logo": restaurant.logo_url,
            "payment_track": payment_track
        },
        "categories": cats,
        "items": items
    }

@router.post("/sessions/start")
async def start_session(data: schemas.SessionStart, db: AsyncSession = Depends(get_db)):
    """
    Start a customer session from a QR token.
    """
    try:
        payload = jwt.decode(data.qr_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != "table":
            raise Exception("Token must be a table QR token")
        table_id = payload.get("sub")
        restaurant_id = payload.get("restaurant_id")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid QR code")
        
    table = await db.get(Table, table_id)
    if not table:
        raise HTTPException(status_code=400, detail="Table not found")

    # Check if there is an active session for this table already
    stmt = select(CustomerSession).where(
        CustomerSession.table_id == table_id,
        CustomerSession.status == SessionStatus.active
    )
    res = await db.execute(stmt)
    existing_session = res.scalar_one_or_none()

    if existing_session:
        # Check if the existing session token is actually expired
        try:
            jwt.decode(existing_session.session_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            # Token is valid, return it
            if table.status != TableStatus.occupied:
                table.status = TableStatus.occupied
                table.occupied_since = datetime.utcnow()
                table.current_session_id = existing_session.id
                await db.commit()
            return {
                "session_token": existing_session.session_token,
                "table_number": table.table_number,
                "session_id": str(existing_session.id)
            }
        except jwt.ExpiredSignatureError:
            # Token expired, close this session and generate a new one
            existing_session.status = SessionStatus.closed
            await db.commit()
        except Exception:
            # Other errors, close it
            existing_session.status = SessionStatus.closed
            await db.commit()
        
    # Generate session token
    session_token = security.create_access_token(
        subject=str(table_id),
        expires_delta=timedelta(hours=24), # Session lasts 24 hours
        extra_claims={"type": "session", "restaurant_id": str(restaurant_id)}
    )
    
    new_session = CustomerSession(
        restaurant_id=restaurant_id,
        table_id=table_id,
        session_token=session_token,
        status=SessionStatus.active
    )
    db.add(new_session)
    await db.flush()
    
    table.status = TableStatus.occupied
    table.occupied_since = datetime.utcnow()
    table.current_session_id = new_session.id
    
    await db.commit()
    return {"session_token": session_token, "table_number": table.table_number, "session_id": str(new_session.id)}


async def validate_session(token: str, db: AsyncSession):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != "session":
            raise Exception()
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid session")
        
    stmt = select(CustomerSession).options(selectinload(CustomerSession.table)).where(CustomerSession.session_token == token, CustomerSession.status == SessionStatus.active)
    res = await db.execute(stmt)
    session = res.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=401, detail="Session expired or closed")
    return session

@router.post("/sessions/{token}/orders")
async def place_order(token: str, data: schemas.OrderCreate, db: AsyncSession = Depends(get_db)):
    """
    Place an order for a session.
    """
    session = await validate_session(token, db)
    restaurant = await db.get(Restaurant, session.restaurant_id)
    
    subtotal = 0
    order_items_data = []
    
    for item_data in data.items:
        menu_item = await db.get(MenuItem, item_data.menu_item_id)
        if not menu_item or not menu_item.is_available:
            raise HTTPException(status_code=400, detail=f"Item {item_data.menu_item_id} unavailable")
            
        item_subtotal = menu_item.price * item_data.quantity
        subtotal += item_subtotal
        
        prep_seconds = (menu_item.preparation_time * 60) if menu_item.preparation_time else 900
        
        order_items_data.append({
            'menu_item_id': menu_item.id,
            'quantity': item_data.quantity,
            'unit_price': menu_item.price,
            'subtotal': item_subtotal,
            'special_instructions': item_data.special_instructions,
            'preparation_time': prep_seconds
        })
        
    from app.services.kitchen_routing import calculate_start_delays
    delayed_items = calculate_start_delays(order_items_data)
    
    order_items = []
    for item in delayed_items:
        order_items.append(OrderItem(
            menu_item_id=item['menu_item_id'],
            quantity=item['quantity'],
            unit_price=item['unit_price'],
            subtotal=item['subtotal'],
            special_instructions=item['special_instructions'],
            status=OrderStatus.received,
            start_delay_seconds=item['start_delay_seconds'],
            estimated_start_at=item['estimated_start_at'],
            estimated_ready_at=item['estimated_ready_at']
        ))
        
    from decimal import Decimal
    tax = subtotal * Decimal("0.16") # 16% VAT
    total = subtotal + tax
    
    # Simple order number generation
    order_number = f"{restaurant.prefix}{datetime.now().strftime('%m%d%H%M%S')}"
    
    new_order = Order(
        restaurant_id=session.restaurant_id,
        table_id=session.table_id,
        session_id=session.id,
        order_number=order_number,
        subtotal=subtotal,
        tax=tax,
        total=total,
        payment_method=data.payment_method,
        status=OrderStatus.received
    )
    db.add(new_order)
    await db.flush()
    
    # Determine pacing preference
    stmt_settings = select(RestaurantSetting).where(
        RestaurantSetting.restaurant_id == restaurant.id,
        RestaurantSetting.key == 'default_pacing'
    )
    default_pacing_setting = (await db.execute(stmt_settings)).scalar_one_or_none()
    default_pacing = default_pacing_setting.value.get("value", "let_customer_choose") if default_pacing_setting else "let_customer_choose"
    
    pacing = data.pacing_preference
    if pacing == 'let_customer_choose' or not pacing:
        pacing = default_pacing
    if pacing == 'let_customer_choose':
        pacing = 'all_together' # fallback
        
    # Group items by course based on category
    def get_course(category_name):
        cat = category_name.lower() if category_name else ""
        if any(x in cat for x in ['appetizer', 'starter', 'soup', 'salad']): return 1, 'Appetizers'
        if any(x in cat for x in ['dessert', 'sweet', 'cake']): return 3, 'Desserts'
        return 2, 'Mains'

    for oi in order_items:
        # fetch category to determine course
        menu_item = await db.get(MenuItem, oi.menu_item_id)
        cat_name = ""
        if menu_item and menu_item.category_id:
            category = await db.get(Category, menu_item.category_id)
            if category: cat_name = category.name
            
        c_num, c_name = get_course(cat_name)
        oi.course_number = c_num
        oi.course_name = c_name
        oi.order_id = new_order.id
        
        if pacing == 'all_together':
            oi.is_fired = True
            oi.fired_at = datetime.utcnow()
        elif pacing == 'in_courses' and c_num == 1:
            oi.is_fired = True
            oi.fired_at = datetime.utcnow()
        else:
            oi.is_fired = False

        db.add(oi)
        
    new_order.pacing_preference = pacing
        
    if data.customer_phone:
        session.customer_phone = data.customer_phone

    if data.payment_method.value == "mpesa":
        try:
            # Assuming phone number is provided in session or data
            phone = data.customer_phone or session.customer_phone or "254700000000" # Fallback or handle properly
            response = await MpesaService.stk_push(phone_number=phone, amount=int(total), order_id=str(new_order.id))
            new_order.payment_status = PaymentStatus.pending
            # Log transaction etc.
        except Exception as e:
            logger.error(f"M-Pesa STK Push failed: {e}")
    
    # Broadcast to kitchen and waiters
    await manager.broadcast(
        {"type": "new_order", "order_id": str(new_order.id), "table": str(session.table_id), "table_number": session.table.table_number if session.table else None},
        f"{session.restaurant_id}_kitchen"
    )
    
    # Broadcast to all station-specific kitchen rooms
    from app.services.kitchen_routing import KitchenRoutingService
    routing_service = KitchenRoutingService(db)
    station_ids = set()
    for oi in order_items:
        sid = await routing_service.get_station_for_item(oi.menu_item_id, session.restaurant_id)
        if sid:
            station_ids.add(str(sid))
            
    for sid in station_ids:
        await manager.broadcast(
            {"type": "new_order", "order_id": str(new_order.id), "table": str(session.table_id), "table_number": session.table.table_number if session.table else None},
            f"{session.restaurant_id}_kitchen_{sid}"
        )
        
    await manager.broadcast(
        {"type": "new_order", "order_id": str(new_order.id), "table": str(session.table_id), "table_number": session.table.table_number if session.table else None},
        f"{session.restaurant_id}_waiters"
    )
    
    # Schedule next course if needed
    if pacing == 'in_courses':
        has_multiple_courses = len(set([oi.course_number for oi in order_items])) > 1
        if has_multiple_courses:
            from app.tasks.worker import schedule_next_course
            stmt_delay = select(RestaurantSetting).where(
                RestaurantSetting.restaurant_id == restaurant.id,
                RestaurantSetting.key == 'auto_fire_delay_minutes'
            )
            delay_setting = (await db.execute(stmt_delay)).scalar_one_or_none()
            delay_minutes = int(delay_setting.value.get("value", 15)) if delay_setting else 15
            schedule_next_course.apply_async(
                args=[str(new_order.id), 2],
                countdown=delay_minutes * 60
            )
    
    await db.commit()
    return {"order_number": order_number, "total": total, "order_id": str(new_order.id)}


@router.post("/sessions/{token}/call-waiter")
async def call_waiter(token: str, data: schemas.WaiterCallCreate, db: AsyncSession = Depends(get_db)):
    """
    Call a waiter to the table.
    """
    session = await validate_session(token, db)
    
    new_call = WaiterCall(
        restaurant_id=session.restaurant_id,
        table_id=session.table_id,
        message=data.message or "Assistance Requested",
        status=CallStatus.pending.value
    )
    db.add(new_call)
    await db.commit()
    
    # Broadcast to waiter station
    await manager.broadcast(
        {"type": "waiter_call", "table_id": str(session.table_id), "table_number": session.table.table_number if session.table else None, "message": data.message or "Assistance Requested"},
        f"{session.restaurant_id}_waiters"
    )
    
    return {"msg": "Waiter called"}

@router.post("/sessions/{token}/request-bill")
async def request_bill(token: str, db: AsyncSession = Depends(get_db)):
    """
    Request bill for the session/table.
    """
    session = await validate_session(token, db)
    
    new_call = WaiterCall(
        restaurant_id=session.restaurant_id,
        table_id=session.table_id,
        message="Bill Requested",
        status=CallStatus.pending.value
    )
    db.add(new_call)
    await db.commit()
    
    # Broadcast to waiter station
    await manager.broadcast(
        {"type": "waiter_call", "table_id": str(session.table_id), "table_number": session.table.table_number if session.table else None, "message": "Bill Requested"},
        f"{session.restaurant_id}_waiters"
    )
    
    return {"msg": "Bill requested"}

@router.get("/sessions/{token}")
async def get_session_details(token: str, db: AsyncSession = Depends(get_db)):
    """
    Get active session details, orders, and total bill.
    """
    session = await validate_session(token, db)
    
    # Get all orders for this session
    stmt = select(Order).where(Order.session_id == session.id, Order.status != OrderStatus.cancelled)
    orders = (await db.execute(stmt)).scalars().all()
    
    # Compile all items
    items = []
    total_amount = 0
    for order in orders:
        total_amount += order.total
        stmt = select(OrderItem).where(OrderItem.order_id == order.id)
        order_items = (await db.execute(stmt)).scalars().all()
        for item in order_items:
            menu_item = await db.get(MenuItem, item.menu_item_id)
            items.append({
                "id": str(item.id),
                "menu_item_id": str(item.menu_item_id),
                "name": menu_item.name if menu_item else "Item",
                "price": float(item.unit_price),
                "quantity": item.quantity,
                "subtotal": float(item.subtotal),
                "special_instructions": item.special_instructions
            })
            
    return {
        "session_id": str(session.id),
        "table_id": str(session.table_id),
        "restaurant_id": str(session.restaurant_id),
        "total_amount": float(total_amount),
        "items": items,
        "orders_count": len(orders)
    }



@router.get("/sessions/{token}/orders/{order_id}", response_model=schemas.OrderRead)
async def get_session_order(token: str, order_id: str, db: AsyncSession = Depends(get_db)):
    """
    Get specific order details for a customer session.
    """
    session = await validate_session(token, db)
    
    stmt = select(Order).options(selectinload(Order.table)).where(
        Order.id == order_id,
        Order.session_id == session.id
    )
    res = await db.execute(stmt)
    order = res.scalar_one_or_none()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    stmt = select(OrderItem).where(OrderItem.order_id == order_id)
    res = await db.execute(stmt)
    order.items = res.scalars().all()
    
    return order
