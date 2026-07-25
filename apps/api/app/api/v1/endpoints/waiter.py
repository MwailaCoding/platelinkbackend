# app/api/v1/endpoints/waiter.py
from typing import List
from datetime import datetime
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.deps import get_db, get_current_user, check_role
from app.models import (
    Order, Staff, Table, WaiterCall, CallStatus, OrderStatus, 
    TableTransferLog, CustomerSession, TableStatus, SessionStatus, Payment, PaymentStatus, PaymentMethod
)
from app.websockets.manager import manager
from app.schemas import schemas
from sqlalchemy.orm import selectinload

router = APIRouter()

@router.get("/tables")
async def get_waiter_tables(
    current_user: Staff = Depends(check_role(["owner", "manager", "waiter"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Get tables assigned to the waiter.
    """
    if not current_user.assigned_tables:
        return []
        
    stmt = select(Table).where(
        Table.restaurant_id == current_user.restaurant_id,
        Table.table_number.in_(current_user.assigned_tables)
    )
    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/orders/new", response_model=List[schemas.OrderRead])
async def get_new_orders(
    current_user: Staff = Depends(check_role(["owner", "manager", "waiter"])),
    db: AsyncSession = Depends(get_db)
):
    """
    New orders waiting to be accepted.
    """
    stmt = select(Order).options(selectinload(Order.table)).where(
        Order.restaurant_id == current_user.restaurant_id,
        Order.status == OrderStatus.received
    ).order_by(Order.created_at.desc())
    
    if current_user.role.value == "waiter":
        assigned_tables = current_user.assigned_tables or []
        if not assigned_tables:
            return []
        stmt = stmt.join(Table).where(Table.table_number.in_(assigned_tables))
        
    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/orders/ready", response_model=List[schemas.OrderRead])
async def get_ready_orders(
    current_user: Staff = Depends(check_role(["owner", "manager", "waiter"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Orders ready for pickup in assigned tables.
    """
    stmt = select(Order).options(selectinload(Order.table)).where(
        Order.restaurant_id == current_user.restaurant_id,
        Order.status == OrderStatus.ready
    ).order_by(Order.created_at.desc())
    
    if current_user.role.value == "waiter":
        assigned_tables = current_user.assigned_tables or []
        if not assigned_tables:
            return []
        stmt = stmt.join(Table).where(Table.table_number.in_(assigned_tables))
        
    result = await db.execute(stmt)
    return result.scalars().all()

@router.put("/orders/{order_id}/served")
async def mark_served(
    order_id: str,
    current_user: Staff = Depends(check_role(["owner", "manager", "waiter"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Waiter marks order as served. Closes the customer session and frees the table.
    """
    import uuid
    try:
        order_uuid = uuid.UUID(order_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid order_id format")

    order = await db.get(Order, order_uuid)
    if not order or order.restaurant_id != current_user.restaurant_id:
        raise HTTPException(status_code=404, detail="Order not found")
        
    order.status = OrderStatus.served
    order.staff_id = current_user.id

    # Find and expire the customer session
    if order.session_id:
        session = await db.get(CustomerSession, order.session_id)
        if session:
            session.status = SessionStatus.closed
            db.add(session)
            
            # Reset table status
            if session.table_id:
                table = await db.get(Table, session.table_id)
                if table:
                    table.status = TableStatus.available
                    table.current_session_id = None
                    db.add(table)
            
            # Broadcast session closed to the customer app
            await manager.broadcast(
                {"type": "session_closed", "session_id": str(session.id)},
                str(current_user.restaurant_id)
            )

    await db.commit()
    
    # Broadcast to KDS to clear order
    await manager.broadcast(
        {"type": "order.picked_up", "order_id": str(order_id)},
        str(current_user.restaurant_id)
    )
    
    return {"msg": "Order served and session closed"}

@router.get("/calls", response_model=List[schemas.WaiterCallRead])
async def get_pending_calls(
    current_user: Staff = Depends(check_role(["owner", "manager", "waiter"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Pending customer assistance calls (excluding bill requests).
    """
    stmt = select(WaiterCall).options(selectinload(WaiterCall.table)).where(
        WaiterCall.restaurant_id == current_user.restaurant_id,
        WaiterCall.status == CallStatus.pending.value,
        WaiterCall.message != "Bill Requested"
    ).order_by(WaiterCall.created_at.desc())
    
    if current_user.role.value == "waiter":
        assigned_tables = current_user.assigned_tables or []
        if not assigned_tables:
            return []
        stmt = stmt.join(Table).where(Table.table_number.in_(assigned_tables))
        
    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/bills", response_model=List[schemas.WaiterCallRead])
async def get_waiter_bills(
    current_user: Staff = Depends(check_role(["owner", "manager", "waiter"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Pending bill requests.
    """
    stmt = select(WaiterCall).options(selectinload(WaiterCall.table)).where(
        WaiterCall.restaurant_id == current_user.restaurant_id,
        WaiterCall.status == CallStatus.pending.value,
        WaiterCall.message == "Bill Requested"
    ).order_by(WaiterCall.created_at.desc())
    
    if current_user.role.value == "waiter":
        assigned_tables = current_user.assigned_tables or []
        if not assigned_tables:
            return []
        stmt = stmt.join(Table).where(Table.table_number.in_(assigned_tables))
        
    result = await db.execute(stmt)
    return result.scalars().all()

@router.put("/calls/{call_id}/acknowledge")
async def acknowledge_call(
    call_id: str,
    current_user: Staff = Depends(check_role(["owner", "manager", "waiter"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Waiter acknowledges the call.
    """
    call = await db.get(WaiterCall, call_id)
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
        
    call.status = CallStatus.acknowledged
    call.acknowledged_by = current_user.id
    call.acknowledged_at = datetime.utcnow()
    
    await db.commit()
    
    # Notify customer via WebSocket
    await manager.broadcast(
        {"type": "call_acknowledged", "waiter_name": current_user.full_name},
        f"session_{call.table_id}"
    )
    
    return {"msg": "Call acknowledged"}


@router.post("/orders/{order_id}/transfer")
async def transfer_order(
    order_id: str,
    payload: schemas.TableTransferRequest,
    current_user: Staff = Depends(check_role(["owner", "manager", "waiter"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Transfer an order and its session to a target table.
    """
    try:
        order_uuid = uuid.UUID(order_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid order_id format")

    order = await db.get(Order, order_uuid)
    if not order or order.restaurant_id != current_user.restaurant_id:
        raise HTTPException(status_code=404, detail="Order not found")

    target_table = await db.get(Table, payload.target_table_id)
    if not target_table or target_table.restaurant_id != current_user.restaurant_id:
        raise HTTPException(status_code=404, detail="Target table not found")

    original_table_id = order.table_id
    original_table = await db.get(Table, original_table_id) if original_table_id else None

    # Shift order and session table_ids
    order.table_id = target_table.id
    
    session = None
    if order.session_id:
        session = await db.get(CustomerSession, order.session_id)
        if session:
            session.table_id = target_table.id

    # Clean up original table
    if original_table:
        original_table.status = TableStatus.available
        original_table.current_session_id = None
        original_table.occupied_since = None

    # Mark target table as occupied
    target_table.status = TableStatus.occupied
    if original_table and original_table.occupied_since:
        target_table.occupied_since = original_table.occupied_since
    else:
        target_table.occupied_since = datetime.utcnow()
    
    if session:
        target_table.current_session_id = session.id

    # Log transfer
    transfer_log = TableTransferLog(
        restaurant_id=current_user.restaurant_id,
        original_table_id=original_table_id,
        new_table_id=target_table.id,
        order_id=order.id,
        transferred_by=current_user.id
    )
    db.add(transfer_log)

    await db.commit()

    # Broadcast websocket update
    await manager.broadcast(
        {
            "type": "table_transferred",
            "order_id": str(order.id),
            "original_table_id": str(original_table_id) if original_table_id else None,
            "new_table_id": str(target_table.id),
            "original_table_number": original_table.table_number if original_table else None,
            "new_table_number": target_table.table_number
        },
        str(current_user.restaurant_id)
    )

    return {"msg": f"Order transferred to table {target_table.table_number}"}


@router.post("/orders/{order_id}/notes")
async def add_order_note(
    order_id: str,
    payload: schemas.OrderNotesRequest,
    current_user: Staff = Depends(check_role(["owner", "manager", "waiter"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Add a note to the order and broadcast to KDS.
    """
    try:
        order_uuid = uuid.UUID(order_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid order_id format")

    order = await db.get(Order, order_uuid)
    if not order or order.restaurant_id != current_user.restaurant_id:
        raise HTTPException(status_code=404, detail="Order not found")

    order.notes = payload.note
    await db.commit()

    # Broadcast order_note_added to KDS
    await manager.broadcast(
        {
            "type": "order_note_added",
            "order_id": str(order.id),
            "waiter_notes": payload.note
        },
        str(current_user.restaurant_id)
    )

    return {"msg": "Note added successfully", "waiter_notes": payload.note}


@router.post("/bills/{order_id}/split-by-item")
async def split_bill_by_item(
    order_id: str,
    payload: schemas.SplitBillRequest,
    current_user: Staff = Depends(check_role(["owner", "manager", "waiter"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Split order bill by item. Deletes any pending payments first, then creates separate Payment records.
    """
    from decimal import Decimal
    try:
        order_uuid = uuid.UUID(order_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid order_id format")

    order = await db.get(Order, order_uuid)
    if not order or order.restaurant_id != current_user.restaurant_id:
        raise HTTPException(status_code=404, detail="Order not found")

    if not payload.splits:
        raise HTTPException(status_code=400, detail="No split data provided")

    # Delete existing pending payments for this order
    stmt = select(Payment).where(
        Payment.order_id == order.id,
        Payment.status == PaymentStatus.pending
    )
    res = await db.execute(stmt)
    pending_payments = res.scalars().all()
    for p in pending_payments:
        await db.delete(p)

    scale_factor = order.total / order.subtotal if order.subtotal > 0 else Decimal("1.16")
    
    created_payments = []
    accumulated_amount = Decimal("0.00")
    num_splits = len(payload.splits)

    for i, split in enumerate(payload.splits):
        if i == num_splits - 1:
            # Last split gets the remainder to avoid rounding issues
            split_amount = order.total - accumulated_amount
        else:
            split_amount = (Decimal(str(split.subtotal)) * scale_factor).quantize(Decimal("0.01"))
            accumulated_amount += split_amount

        # Create Payment record
        payment = Payment(
            restaurant_id=order.restaurant_id,
            order_id=order.id,
            amount=split_amount,
            payment_method=PaymentMethod.cash,  # default
            status=PaymentStatus.pending,
            transaction_id=f"SPLIT-{order.order_number}-{i+1}-{uuid.uuid4().hex[:6].upper()}"
        )
        db.add(payment)
        created_payments.append(payment)

    await db.commit()

    return {
        "msg": "Bill split successfully",
        "payments": [
            {"payment_id": str(p.id), "amount": float(p.amount), "transaction_id": p.transaction_id}
            for p in created_payments
        ]
    }

