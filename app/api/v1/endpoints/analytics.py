# app/api/v1/endpoints/analytics.py
from datetime import datetime, date
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, Date
from app.core.deps import get_db, get_current_user, check_role
from app.models import Order, Staff, Table, MenuItem, OrderStatus
from app.schemas import schemas

router = APIRouter()

@router.get("/dashboard", response_model=schemas.DashboardStats)
async def get_dashboard_stats(current_user: Staff = Depends(check_role(["owner", "manager"])), db: AsyncSession = Depends(get_db)):
    rid = current_user.restaurant_id
    today = date.today()
    
    today_sales = (await db.execute(select(func.sum(Order.total)).where(Order.restaurant_id == rid, func.cast(Order.created_at, Date) == today, Order.payment_status == "paid"))).scalar() or 0
    today_orders = (await db.execute(select(func.count(Order.id)).where(Order.restaurant_id == rid, func.cast(Order.created_at, Date) == today))).scalar() or 0
    active_tables = (await db.execute(select(func.count(Table.id)).where(Table.restaurant_id == rid, Table.status != "available"))).scalar() or 0
    low_stock_count = (await db.execute(select(func.count(MenuItem.id)).where(MenuItem.restaurant_id == rid, MenuItem.stock_quantity <= MenuItem.low_stock_threshold))).scalar() or 0
    
    pending_stmt = select(func.count(Order.id)).where(Order.restaurant_id == rid, Order.status.in_([OrderStatus.received, OrderStatus.preparing, OrderStatus.ready]))
    pending_orders = (await db.execute(pending_stmt)).scalar() or 0
    
    return {
        "today_sales": today_sales,
        "today_orders": today_orders,
        "active_tables": active_tables,
        "low_stock_count": low_stock_count,
        "pending_orders": pending_orders
    }


@router.get("/waiter-sales")
async def get_waiter_sales_report(
    start_date: str = None,
    end_date: str = None,
    current_user: Staff = Depends(check_role(["owner", "manager"])),
    db: AsyncSession = Depends(get_db)
):
    from datetime import timedelta
    rid = current_user.restaurant_id
    
    stmt = select(
        Staff.id.label("waiter_id"),
        Staff.full_name.label("waiter_name"),
        func.count(Order.id).label("total_orders"),
        func.sum(Order.total).label("total_sales"),
        func.avg(Order.total).label("average_ticket")
    ).join(
        Order, Order.staff_id == Staff.id
    ).where(
        Order.restaurant_id == rid,
        Order.payment_status == "paid"
    )
    
    if start_date:
        try:
            parsed_start = datetime.strptime(start_date, "%Y-%m-%d")
            stmt = stmt.where(Order.created_at >= parsed_start)
        except ValueError:
            pass
            
    if end_date:
        try:
            parsed_end = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
            stmt = stmt.where(Order.created_at < parsed_end)
        except ValueError:
            pass

    stmt = stmt.group_by(Staff.id, Staff.full_name)
    res = await db.execute(stmt)
    rows = res.all()
    
    return [
        {
            "waiter_id": str(row.waiter_id),
            "waiter_name": row.waiter_name,
            "total_orders": row.total_orders,
            "total_sales": float(row.total_sales) if row.total_sales else 0.0,
            "average_ticket": float(row.average_ticket) if row.average_ticket else 0.0
        }
        for row in rows
    ]

@router.get("/total-sales")
async def get_total_sales_across_branches(
    db: AsyncSession = Depends(get_db),
    current_staff: Staff = Depends(check_role(["owner"]))
):
    """Get total sales across all branches (Owner only)"""
    from app.models import Branches, PaymentStatus
    
    today = date.today()
    
    # Total sales
    total_sales_stmt = select(func.sum(Order.total)).where(
        Order.restaurant_id == current_staff.restaurant_id,
        func.cast(Order.created_at, Date) == today,
        Order.payment_status == PaymentStatus.paid
    )
    total_sales = (await db.execute(total_sales_stmt)).scalar() or 0
    
    # Get sales per branch
    branch_sales_stmt = select(
        Branches.id,
        Branches.name,
        func.sum(Order.total).label('sales')
    ).outerjoin(
        Order, (Order.branch_id == Branches.id) & 
               (func.cast(Order.created_at, Date) == today) & 
               (Order.payment_status == PaymentStatus.paid)
    ).where(
        Branches.restaurant_id == current_staff.restaurant_id,
        Branches.is_active == True
    ).group_by(Branches.id, Branches.name)
    
    branch_sales = (await db.execute(branch_sales_stmt)).all()
    
    return {
        "total_sales": float(total_sales),
        "branches": [
            {"id": str(b.id), "name": b.name, "sales": float(b.sales) if b.sales else 0.0}
            for b in branch_sales
        ]
    }
