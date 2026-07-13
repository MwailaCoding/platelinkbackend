from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
import uuid

from app.core.deps import get_db
from models import Branches, Restaurant, Staff, Table, MenuItem, Order
from app.core.deps import get_current_active_staff as get_current_staff

router = APIRouter(prefix="/branches", tags=["Branches"])

class CreateBranchRequest(BaseModel):
    name: str
    address: Optional[str] = None
    city: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    copy_tables_from_branch_id: Optional[str] = None
    copy_menu_from_branch_id: Optional[str] = None
    number_of_tables: int = 10

class UpdateBranchRequest(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    is_active: Optional[bool] = None

class CopyMenuRequest(BaseModel):
    source_branch_id: str

class SyncMenuRequest(BaseModel):
    branch_ids: List[str]

# ============================================================
# BRANCH CRUD (Owner Only)
# ============================================================

@router.get("/")
async def get_branches(
    db: Session = Depends(get_db),
    current_staff: Staff = Depends(get_current_staff)
):
    """Get all branches for this restaurant group"""
    
    if current_staff.role_type == 'owner' or current_staff.role.value == 'owner':
        restaurant_id = current_staff.restaurant_id
        branches = db.query(Branches).filter(
            Branches.restaurant_id == restaurant_id
        ).order_by(Branches.created_at).all()
        
        main_restaurant = db.query(Restaurant).filter(
            Restaurant.id == restaurant_id
        ).first()
        
        result = []
        if main_restaurant:
            result.append({
                "id": str(main_restaurant.id),
                "name": main_restaurant.name,
                "is_main": True,
                "address": main_restaurant.address,
                "phone": main_restaurant.phone,
                "is_active": True
            })
        
        for branch in branches:
            result.append({
                "id": str(branch.id),
                "name": branch.name,
                "is_main": False,
                "address": branch.address,
                "phone": branch.phone,
                "is_active": branch.is_active
            })
        
        return result
    
    elif current_staff.role_type == 'branch_manager' or current_staff.role.value == 'branch_manager':
        branch = db.query(Branches).filter(
            Branches.id == current_staff.branch_id
        ).first()
        if branch:
            return [{
                "id": str(branch.id),
                "name": branch.name,
                "is_main": False,
                "address": branch.address,
                "phone": branch.phone,
                "is_active": branch.is_active
            }]
    
    return []

@router.post("/")
async def create_branch(
    request: CreateBranchRequest,
    db: Session = Depends(get_db),
    current_staff: Staff = Depends(get_current_staff)
):
    """Create a new branch (Owner only)"""
    
    if current_staff.role_type != 'owner' and current_staff.role.value != 'owner':
        raise HTTPException(403, "Only owner can create branches")
    
    new_branch = Branches(
        restaurant_id=current_staff.restaurant_id,
        name=request.name,
        address=request.address,
        city=request.city,
        phone=request.phone,
        email=request.email
    )
    db.add(new_branch)
    db.flush()
    
    if request.copy_tables_from_branch_id:
        source_tables = db.query(Table).filter(
            Table.branch_id == request.copy_tables_from_branch_id
        ).all()
        
        for table in source_tables:
            new_table = Table(
                restaurant_id=current_staff.restaurant_id,
                branch_id=new_branch.id,
                table_number=table.table_number,
                capacity=table.capacity,
                status='available',
                qr_code_url=table.qr_code_url
            )
            db.add(new_table)
    else:
        for i in range(1, request.number_of_tables + 1):
            new_table = Table(
                restaurant_id=current_staff.restaurant_id,
                branch_id=new_branch.id,
                table_number=i,
                capacity=4,
                status='available'
            )
            db.add(new_table)
            
    if request.copy_menu_from_branch_id:
        copy_menu_to_branch_internal(db, request.copy_menu_from_branch_id, new_branch.id)
    
    db.query(Restaurant).filter(
        Restaurant.id == current_staff.restaurant_id
    ).update({"is_multi_branch": True})
    
    db.commit()
    
    return {"success": True, "branch_id": str(new_branch.id)}

@router.put("/{branch_id}")
async def update_branch(
    branch_id: str,
    request: UpdateBranchRequest,
    db: Session = Depends(get_db),
    current_staff: Staff = Depends(get_current_staff)
):
    """Update branch details (Owner only)"""
    
    if current_staff.role_type != 'owner' and current_staff.role.value != 'owner':
        raise HTTPException(403, "Only owner can update branches")
    
    branch = db.query(Branches).filter(Branches.id == branch_id).first()
    if not branch:
        raise HTTPException(404, "Branch not found")
    
    if request.name:
        branch.name = request.name
    if request.address:
        branch.address = request.address
    if request.city:
        branch.city = request.city
    if request.phone:
        branch.phone = request.phone
    if request.email:
        branch.email = request.email
    if request.is_active is not None:
        branch.is_active = request.is_active
    
    branch.updated_at = datetime.utcnow()
    db.commit()
    
    return {"success": True}

@router.delete("/{branch_id}")
async def delete_branch(
    branch_id: str,
    db: Session = Depends(get_db),
    current_staff: Staff = Depends(get_current_staff)
):
    """Deactivate branch (Owner only)"""
    
    if current_staff.role_type != 'owner' and current_staff.role.value != 'owner':
        raise HTTPException(403, "Only owner can delete branches")
    
    branch = db.query(Branches).filter(Branches.id == branch_id).first()
    if not branch:
        raise HTTPException(404, "Branch not found")
    
    branch.is_active = False
    db.commit()
    
    return {"success": True}

@router.get("/{branch_id}/dashboard")
async def get_branch_dashboard(
    branch_id: str,
    db: Session = Depends(get_db),
    current_staff: Staff = Depends(get_current_staff)
):
    """Get dashboard data for a specific branch"""
    
    if current_staff.role_type == 'owner' or current_staff.role.value == 'owner':
        branch = db.query(Branches).filter(
            Branches.id == branch_id,
            Branches.restaurant_id == current_staff.restaurant_id
        ).first()
    elif current_staff.role_type == 'branch_manager' or current_staff.role.value == 'branch_manager':
        if str(current_staff.branch_id) != branch_id:
            raise HTTPException(403, "Access denied")
        branch = db.query(Branches).filter(Branches.id == branch_id).first()
    else:
        raise HTTPException(403, "Access denied")
    
    if not branch or not branch.is_active:
        raise HTTPException(404, "Branch not found")
    
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_sales = db.query(func.sum(Order.total)).filter(
        Order.branch_id == branch_id,
        Order.created_at >= today_start,
        Order.payment_status == 'paid'
    ).scalar() or 0
    
    active_orders = db.query(Order).filter(
        Order.branch_id == branch_id,
        Order.status.in_(['received', 'preparing', 'ready'])
    ).count()
    
    total_tables = db.query(Table).filter(Table.branch_id == branch_id).count()
    occupied_tables = db.query(Table).filter(
        Table.branch_id == branch_id,
        Table.status.in_(['occupied', 'ordering', 'ordered', 'eating'])
    ).count()
    
    return {
        "branch_id": str(branch.id),
        "branch_name": branch.name,
        "today_sales": float(today_sales),
        "active_orders": active_orders,
        "total_tables": total_tables,
        "occupied_tables": occupied_tables
    }

@router.post("/{branch_id}/copy-menu")
async def copy_menu_to_branch(
    branch_id: str,
    request: CopyMenuRequest,
    db: Session = Depends(get_db),
    current_staff: Staff = Depends(get_current_staff)
):
    """Copy menu from another branch"""
    
    if current_staff.role_type != 'owner' and current_staff.role.value != 'owner':
        raise HTTPException(403, "Only owner can copy menu")
    
    copy_menu_to_branch_internal(db, request.source_branch_id, branch_id)
    
    return {"success": True}

@router.post("/menu/sync")
async def sync_menu_to_branches(
    request: SyncMenuRequest,
    db: Session = Depends(get_db),
    current_staff: Staff = Depends(get_current_staff)
):
    """Sync menu changes to selected branches"""
    
    if current_staff.role_type != 'owner' and current_staff.role.value != 'owner':
        raise HTTPException(403, "Only owner can sync menu")
    
    source_items = db.query(MenuItem).filter(
        MenuItem.restaurant_id == current_staff.restaurant_id,
        MenuItem.branch_id.is_(None)
    ).all()
    
    for branch_id in request.branch_ids:
        branch = db.query(Branches).filter(Branches.id == branch_id).first()
        if branch:
            db.query(MenuItem).filter(
                MenuItem.branch_id == branch_id
            ).delete()
            
            for source_item in source_items:
                new_item = MenuItem(
                    restaurant_id=current_staff.restaurant_id,
                    branch_id=branch_id,
                    category_id=source_item.category_id,
                    name=source_item.name,
                    description=source_item.description,
                    price=source_item.price,
                    image_url=source_item.image_url,
                    is_available=source_item.is_available,
                    preparation_time=source_item.preparation_time,
                    display_order=source_item.display_order
                )
                db.add(new_item)
    
    db.commit()
    
    return {"success": True, "synced_branches": len(request.branch_ids)}

@router.post("/{branch_id}/sync-menu")
async def sync_menu_for_single_branch(
    branch_id: str,
    db: Session = Depends(get_db),
    current_staff: Staff = Depends(get_current_staff)
):
    """Sync menu changes to a specific branch"""
    
    if current_staff.role_type != 'owner' and current_staff.role.value != 'owner':
        raise HTTPException(403, "Only owner can sync menu")
    
    source_items = db.query(MenuItem).filter(
        MenuItem.restaurant_id == current_staff.restaurant_id,
        MenuItem.branch_id.is_(None)
    ).all()
    
    branch = db.query(Branches).filter(Branches.id == branch_id).first()
    if not branch:
        raise HTTPException(404, "Branch not found")

    db.query(MenuItem).filter(
        MenuItem.branch_id == branch_id
    ).delete()
    
    for source_item in source_items:
        new_item = MenuItem(
            restaurant_id=current_staff.restaurant_id,
            branch_id=branch_id,
            category_id=source_item.category_id,
            name=source_item.name,
            description=source_item.description,
            price=source_item.price,
            image_url=source_item.image_url,
            is_available=source_item.is_available,
            preparation_time=source_item.preparation_time,
            display_order=source_item.display_order
        )
        db.add(new_item)
    
    db.commit()
    return {"success": True}

def copy_menu_to_branch_internal(db: Session, source_branch_id: str, target_branch_id: str):
    source_items = db.query(MenuItem).filter(
        MenuItem.branch_id == source_branch_id
    ).all()
    
    for source_item in source_items:
        new_item = MenuItem(
            restaurant_id=source_item.restaurant_id,
            branch_id=target_branch_id,
            category_id=source_item.category_id,
            name=source_item.name,
            description=source_item.description,
            price=source_item.price,
            image_url=source_item.image_url,
            is_available=source_item.is_available,
            preparation_time=source_item.preparation_time,
            display_order=source_item.display_order
        )
        db.add(new_item)
