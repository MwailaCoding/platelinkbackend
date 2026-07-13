# app/api/v1/endpoints/orders.py
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from app.core.deps import get_db, get_current_user, check_role
from app.models import Order, OrderItem, Staff, OrderStatus, ActivityLog, TableStatus
from app.schemas import schemas
from app.websockets.manager import manager

router = APIRouter()

@router.get("/", response_model=List[schemas.OrderRead])
async def list_orders(
    status: Optional[OrderStatus] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: Staff = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List and filter orders.
    """
    stmt = select(Order).options(selectinload(Order.table)).where(Order.restaurant_id == current_user.restaurant_id)
    if status:
        stmt = stmt.where(Order.status == status)
    if start_date:
        stmt = stmt.where(Order.created_at >= start_date)
    if end_date:
        stmt = stmt.where(Order.created_at <= end_date)
    
    stmt = stmt.order_by(Order.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/{order_id}", response_model=schemas.OrderRead)
async def get_order(
    order_id: str,
    current_user: Staff = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get order details.
    """
    stmt = select(Order).options(selectinload(Order.table)).where(Order.id == order_id)
    res = await db.execute(stmt)
    order = res.scalar_one_or_none()
    if not order or order.restaurant_id != current_user.restaurant_id:
        raise HTTPException(status_code=404, detail="Order not found")
        
    stmt = select(OrderItem).where(OrderItem.order_id == order_id)
    res = await db.execute(stmt)
    order.items = res.scalars().all()
    return order

@router.put("/{order_id}/status")
async def update_order_status(
    order_id: str,
    status_data: OrderStatus = Body(..., embed=True),
    current_user: Staff = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update order status and notify via WebSockets.
    """
    stmt = select(Order).options(selectinload(Order.table)).where(Order.id == order_id)
    res = await db.execute(stmt)
    order = res.scalar_one_or_none()
    if not order or order.restaurant_id != current_user.restaurant_id:
        raise HTTPException(status_code=404, detail="Order not found")
        
    # Validation logic for transitions would go here
    order.status = status_data
    if status_data == OrderStatus.completed:
        order.completed_at = datetime.utcnow()
        
    await manager.broadcast(
        {"type": "order_status", "order_id": str(order.id), "status": status_data.value, "table_number": order.table_number},
        str(current_user.restaurant_id)
    )
    
    db.add(ActivityLog(
        restaurant_id=current_user.restaurant_id,
        staff_id=current_user.id,
        action=f"order_status_{status_data.value}"
    ))
    
    await db.commit()
    return {"msg": "Status updated"}

@router.post("/{order_id}/cancel")
async def cancel_order(
    order_id: str,
    reason: str = Body(..., embed=True),
    current_user: Staff = Depends(check_role(["owner", "manager"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Cancel an order.
    """
    stmt = select(Order).options(selectinload(Order.table)).where(Order.id == order_id)
    res = await db.execute(stmt)
    order = res.scalar_one_or_none()
    if not order or order.restaurant_id != current_user.restaurant_id:
        raise HTTPException(status_code=404, detail="Order not found")
        
    if order.status in [OrderStatus.completed, OrderStatus.served]:
        raise HTTPException(status_code=400, detail="Cannot cancel a served order")
        
    order.status = OrderStatus.cancelled
    db.add(ActivityLog(
        restaurant_id=current_user.restaurant_id,
        staff_id=current_user.id,
        action="order_cancelled",
        metadata_info={"reason": reason}
    ))
    
    await manager.broadcast(
        {"type": "order_cancelled", "order_id": str(order.id), "table_number": order.table_number},
        str(current_user.restaurant_id)
    )
    
    await db.commit()
    return {"msg": "Order cancelled"}

@router.get("/active/queue", response_model=List[schemas.OrderRead])
async def get_active_orders(
    current_user: Staff = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get active orders for kitchen/waiter views.
    """
    stmt = select(Order).options(selectinload(Order.table)).where(
        Order.restaurant_id == current_user.restaurant_id,
        Order.status.in_([OrderStatus.received, OrderStatus.preparing, OrderStatus.ready])
    ).order_by(Order.created_at.asc())
    
    result = await db.execute(stmt)
    return result.scalars().all()

from app.models import Table, CustomerSession, TableTransferLog, ItemTransferLog
from sqlalchemy import update

@router.post("/transfer-table")
async def transfer_table(
    req: schemas.TableTransferRequest,
    source_table_id: UUID = Query(...),
    current_user: Staff = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    source_table = await db.get(Table, source_table_id)
    target_table = await db.get(Table, req.target_table_id)
    
    if not source_table or not target_table:
        raise HTTPException(status_code=404, detail="Table not found")
        
    if source_table.restaurant_id != current_user.restaurant_id or target_table.restaurant_id != current_user.restaurant_id:
        raise HTTPException(status_code=403, detail="Forbidden")
        
    if target_table.status != TableStatus.available:
        raise HTTPException(status_code=400, detail="Target table is not available")
        
    if not source_table.current_session_id:
        raise HTTPException(status_code=400, detail="Source table has no active session")
        
    session_id = source_table.current_session_id
    
    # Update orders
    stmt = update(Order).where(Order.session_id == session_id).values(table_id=target_table.id)
    await db.execute(stmt)
    
    # Update session
    stmt = update(CustomerSession).where(CustomerSession.id == session_id).values(table_id=target_table.id)
    await db.execute(stmt)
    
    # Update tables
    target_table.current_session_id = session_id
    target_table.status = source_table.status
    target_table.occupied_since = source_table.occupied_since
    
    source_table.current_session_id = None
    source_table.status = TableStatus.available
    source_table.occupied_since = None
    
    # Log transfer
    log = TableTransferLog(
        restaurant_id=current_user.restaurant_id,
        original_table_id=source_table.id,
        new_table_id=target_table.id,
        session_id=session_id,
        transferred_by_staff_id=current_user.id
    )
    db.add(log)
    
    await db.commit()
    return {"msg": "Table transferred successfully"}

@router.post("/transfer-items")
async def transfer_items(
    req: schemas.ItemTransferRequest,
    source_table_id: UUID = Query(...),
    current_user: Staff = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Retrieve order items and update their order_id to match target table's active order
    # (Simplified: typically you create a new order on target table or use existing)
    target_table = await db.get(Table, req.target_table_id)
    if not target_table or target_table.restaurant_id != current_user.restaurant_id:
        raise HTTPException(status_code=404, detail="Target table not found")
        
    # Find active order on target table
    stmt = select(Order).where(Order.table_id == target_table.id, Order.status.in_([OrderStatus.received, OrderStatus.pending, OrderStatus.preparing, OrderStatus.ready, OrderStatus.served]))
    res = await db.execute(stmt)
    target_order = res.scalar_one_or_none()
    
    if not target_order:
        # Create new order
        target_order = Order(
            restaurant_id=current_user.restaurant_id,
            table_id=target_table.id,
            session_id=target_table.current_session_id,
            staff_id=current_user.id
        )
        db.add(target_order)
        await db.flush()
        
    for item_id in req.item_ids:
        item = await db.get(OrderItem, item_id)
        if item:
            item.order_id = target_order.id
            log = ItemTransferLog(
                restaurant_id=current_user.restaurant_id,
                order_item_id=item.id,
                source_table_id=source_table_id,
                target_table_id=target_table.id,
                transferred_by=current_user.id
            )
            db.add(log)
            
    await db.commit()
    return {"msg": "Items transferred"}

@router.post("/split-bill")
async def split_bill(
    order_id: UUID,
    req: schemas.SplitBillRequest,
    current_user: Staff = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Splits the bill into separate orders or payments
    # (Placeholder logic for creating new orders per split)
    original_order = await db.get(Order, order_id)
    if not original_order or original_order.restaurant_id != current_user.restaurant_id:
        raise HTTPException(status_code=404, detail="Order not found")
        
    for split in req.splits:
        # Create a split order
        new_order = Order(
            restaurant_id=current_user.restaurant_id,
            table_id=original_order.table_id,
            session_id=original_order.session_id,
            subtotal=split.subtotal,
            total=split.subtotal,
            order_number=f"{original_order.order_number}-{split.customer_name}"
        )
        db.add(new_order)
        await db.flush()
        
        for item_id in split.item_ids:
            item = await db.get(OrderItem, item_id)
            if item and item.order_id == order_id:
                item.order_id = new_order.id
                
    await db.commit()
    return {"msg": "Bill split successfully"}

@router.post("/{order_id}/hold")
async def hold_order(
    order_id: UUID,
    reason: str = Body(..., embed=True),
    resume_at: Optional[datetime] = Body(None, embed=True),
    current_user: Staff = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    order = await db.get(Order, order_id)
    if not order or order.restaurant_id != current_user.restaurant_id:
        raise HTTPException(status_code=404, detail="Order not found")
        
    stmt = select(OrderItem).where(OrderItem.order_id == order_id)
    res = await db.execute(stmt)
    items = res.scalars().all()
    
    for item in items:
        item.is_held = True
        item.hold_reason = reason
        item.hold_started_at = datetime.utcnow()
        if resume_at:
            item.hold_resume_at = resume_at
            
    await db.commit()
    return {"msg": "Order put on hold"}

@router.put("/{order_id}/pacing")
async def change_order_pacing(
    order_id: UUID,
    request: schemas.ChangePacingRequest,
    db: AsyncSession = Depends(get_db)
):
    """Customer changes pacing preference mid-meal"""
    order = await db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    old_pacing = order.pacing_preference
    new_pacing = request.pacing
    
    if old_pacing == new_pacing:
        return {"message": "No change needed"}
        
    order.pacing_preference = new_pacing
    
    if new_pacing == 'all_together':
        # Fire all remaining unfired courses
        stmt = select(OrderItem).where(
            OrderItem.order_id == order_id,
            OrderItem.is_fired == False
        )
        items = (await db.execute(stmt)).scalars().all()
        for item in items:
            item.is_fired = True
            item.fired_at = datetime.utcnow()
            
        if items:
            await manager.broadcast_to_kitchen(str(order.restaurant_id), {
                "type": "course.fired",
                "order_id": str(order_id),
                "course": "all_remaining"
            })
    else:
        # If switching to in_courses, just fire next course if none are currently cooking
        stmt = select(OrderItem).where(
            OrderItem.order_id == order_id,
            OrderItem.is_fired == False
        ).order_by(OrderItem.course_number.asc())
        next_item = (await db.execute(stmt)).scalars().first()
        
        if next_item:
            next_course = next_item.course_number
            course_items_stmt = select(OrderItem).where(
                OrderItem.order_id == order_id,
                OrderItem.course_number == next_course,
                OrderItem.is_fired == False
            )
            course_items = (await db.execute(course_items_stmt)).scalars().all()
            for item in course_items:
                item.is_fired = True
                item.fired_at = datetime.utcnow()
                
            if course_items:
                await manager.broadcast_to_kitchen(str(order.restaurant_id), {
                    "type": "course.fired",
                    "order_id": str(order_id),
                    "course": next_course
                })
                
    await db.commit()
    return {"success": True, "new_pacing": new_pacing}
