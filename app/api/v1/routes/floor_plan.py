from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Response
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import json
from pydantic import BaseModel

from app.core.deps import get_db
from models import Restaurant, Floors, Table as Tables, FloorElements
from app.core.deps import get_current_user as get_current_restaurant

router = APIRouter(prefix="/floor-plan", tags=["Floor Plan"])

# Pydantic models for request bodies
class CreateFloorRequest(BaseModel):
    name: str
    display_order: Optional[int] = 0
    background_image_url: Optional[str] = None
    width: Optional[int] = 1200
    height: Optional[int] = 800

class UpdateFloorRequest(BaseModel):
    name: Optional[str] = None
    display_order: Optional[int] = None
    is_active: Optional[bool] = None
    background_image_url: Optional[str] = None

class FloorOrderItem(BaseModel):
    id: str
    order: int

class ReorderFloorsRequest(BaseModel):
    orders: List[FloorOrderItem]

class TablePosition(BaseModel):
    id: str
    x: int
    y: int

class UpdateTablePositionsRequest(BaseModel):
    floor_id: str
    tables: List[TablePosition]

class ElementData(BaseModel):
    x1: Optional[float] = None
    y1: Optional[float] = None
    x2: Optional[float] = None
    y2: Optional[float] = None
    x: Optional[float] = None
    y: Optional[float] = None
    width: Optional[float] = None
    height: Optional[float] = None
    thickness: Optional[float] = None

class CreateElementRequest(BaseModel):
    floor_id: str
    element_type: str
    element_data: ElementData

class PrintRequest(BaseModel):
    include_table_numbers: Optional[bool] = True
    include_capacities: Optional[bool] = True
    include_legend: Optional[bool] = True

class TablePrintItem(BaseModel):
    id: str
    table_number: int

class BatchPrintSignsRequest(BaseModel):
    tables: List[TablePrintItem]
    template: Optional[str] = 'default'

class CopyFloorRequest(BaseModel):
    new_name: str
    display_order: int

# ============================================================
# FLOOR MANAGEMENT
# ============================================================

@router.get("/floors")
async def get_floors(
    db: Session = Depends(get_db),
    restaurant: Restaurant = Depends(get_current_restaurant)
):
    """Get all floors for this restaurant"""
    floors = db.query(Floors).filter(
        Floors.restaurant_id == restaurant.id
    ).order_by(Floors.display_order).all()
    
    return [
        {
            "id": floor.id,
            "name": floor.name,
            "display_order": floor.display_order,
            "is_active": floor.is_active,
            "background_image_url": floor.background_image_url,
            "width": floor.width,
            "height": floor.height
        }
        for floor in floors
    ]

@router.post("/floors")
async def create_floor(
    request: CreateFloorRequest,
    db: Session = Depends(get_db),
    restaurant: Restaurant = Depends(get_current_restaurant)
):
    """Create a new floor (Ground Floor, Upper Floor, Outdoor Patio, etc.)"""
    
    floor = Floors(
        restaurant_id=restaurant.id,
        name=request.name,
        display_order=request.display_order or 0,
        background_image_url=request.background_image_url,
        width=request.width or 1200,
        height=request.height or 800
    )
    db.add(floor)
    db.commit()
    db.refresh(floor)
    
    return {"success": True, "floor": floor}

@router.put("/floors/{floor_id}")
async def update_floor(
    floor_id: str,
    request: UpdateFloorRequest,
    db: Session = Depends(get_db),
    restaurant: Restaurant = Depends(get_current_restaurant)
):
    """Update floor properties"""
    
    floor = db.query(Floors).filter(
        Floors.id == floor_id,
        Floors.restaurant_id == restaurant.id
    ).first()
    
    if not floor:
        raise HTTPException(404, "Floor not found")
    
    if request.name:
        floor.name = request.name
    if request.display_order is not None:
        floor.display_order = request.display_order
    if request.is_active is not None:
        floor.is_active = request.is_active
    if request.background_image_url is not None:
        floor.background_image_url = request.background_image_url
    
    floor.updated_at = datetime.utcnow()
    db.commit()
    
    return {"success": True}

@router.delete("/floors/{floor_id}")
async def delete_floor(
    floor_id: str,
    db: Session = Depends(get_db),
    restaurant: Restaurant = Depends(get_current_restaurant)
):
    """Delete a floor (moves tables to default floor)"""
    
    floor = db.query(Floors).filter(
        Floors.id == floor_id,
        Floors.restaurant_id == restaurant.id
    ).first()
    
    if not floor:
        raise HTTPException(404, "Floor not found")
    
    # Move tables to another floor or mark as no floor
    db.query(Tables).filter(Tables.floor_id == floor_id).update(
        {"floor_id": None}
    )
    
    db.delete(floor)
    db.commit()
    
    return {"success": True}

@router.post("/floors/reorder")
async def reorder_floors(
    request: ReorderFloorsRequest,
    db: Session = Depends(get_db),
    restaurant: Restaurant = Depends(get_current_restaurant)
):
    """Update display order of floors"""
    
    for item in request.orders:
        db.query(Floors).filter(
            Floors.id == item.id,
            Floors.restaurant_id == restaurant.id
        ).update({"display_order": item.order})
    
    db.commit()
    
    return {"success": True}

@router.post("/floors/{floor_id}/upload-background")
async def upload_floor_background(
    floor_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    restaurant: Restaurant = Depends(get_current_restaurant)
):
    """Upload floor plan blueprint image"""
    
    floor = db.query(Floors).filter(
        Floors.id == floor_id,
        Floors.restaurant_id == restaurant.id
    ).first()
    
    if not floor:
        raise HTTPException(404, "Floor not found")
    
    # Mocking upload result since we don't have cloudinary configured here
    # upload_result = await upload_to_cloudinary(file, f"floor_plans/{restaurant.id}/{floor_id}")
    
    floor.background_image_url = "mock_url"
    db.commit()
    
    return {"background_image_url": floor.background_image_url}

# ============================================================
# TABLE POSITIONING
# ============================================================

@router.get("/tables/{floor_id}")
async def get_tables_on_floor(
    floor_id: str,
    db: Session = Depends(get_db),
    restaurant: Restaurant = Depends(get_current_restaurant)
):
    """Get all tables on a specific floor with positions"""
    
    tables = db.query(Tables).filter(
        Tables.restaurant_id == restaurant.id,
        Tables.floor_id == floor_id
    ).all()
    
    return [
        {
            "id": table.id,
            "table_number": table.table_number,
            "capacity": table.capacity,
            "status": table.status,
            "pos_x": table.pos_x,
            "pos_y": table.pos_y,
            "shape": table.shape,
            "width": table.width,
            "height": table.height,
            "qr_code_url": table.qr_code_url
        }
        for table in tables
    ]

@router.put("/tables/positions")
async def update_table_positions(
    request: UpdateTablePositionsRequest,
    db: Session = Depends(get_db),
    restaurant: Restaurant = Depends(get_current_restaurant)
):
    """Batch update table positions (for drag-drop save)"""
    
    for item in request.tables:
        db.query(Tables).filter(
            Tables.id == item.id,
            Tables.restaurant_id == restaurant.id
        ).update({
            "pos_x": item.x,
            "pos_y": item.y,
            "floor_id": request.floor_id
        })
    
    db.commit()
    
    return {"success": True, "updated_count": len(request.tables)}

# ============================================================
# FLOOR ELEMENTS (Walls, Doors, Windows)
# ============================================================

@router.get("/elements/{floor_id}")
async def get_floor_elements(
    floor_id: str,
    db: Session = Depends(get_db),
    restaurant: Restaurant = Depends(get_current_restaurant)
):
    """Get all elements (walls, doors, windows) on a floor"""
    
    elements = db.query(FloorElements).filter(
        FloorElements.floor_id == floor_id
    ).all()
    
    return [
        {
            "id": element.id,
            "type": element.element_type,
            "data": element.element_data
        }
        for element in elements
    ]

@router.post("/elements")
async def create_floor_element(
    request: CreateElementRequest,
    db: Session = Depends(get_db),
    restaurant: Restaurant = Depends(get_current_restaurant)
):
    """Add a wall, door, or window to the floor plan"""
    
    element = FloorElements(
        floor_id=request.floor_id,
        element_type=request.element_type,
        element_data=request.element_data.dict(exclude_unset=True)
    )
    db.add(element)
    db.commit()
    
    return {"success": True, "element": element}

@router.delete("/elements/{element_id}")
async def delete_floor_element(
    element_id: str,
    db: Session = Depends(get_db),
    restaurant: Restaurant = Depends(get_current_restaurant)
):
    """Remove a floor element"""
    
    element = db.query(FloorElements).filter(
        FloorElements.id == element_id
    ).first()
    
    if not element:
        raise HTTPException(404, "Element not found")
    
    db.delete(element)
    db.commit()
    
    return {"success": True}

# ============================================================
# PRINTING & EXPORT
# ============================================================

@router.post("/print/{floor_id}")
async def print_floor_plan(
    floor_id: str,
    request: PrintRequest,
    db: Session = Depends(get_db),
    restaurant: Restaurant = Depends(get_current_restaurant)
):
    """Generate PDF for printing floor plan"""
    
    floor = db.query(Floors).filter(Floors.id == floor_id).first()
    tables = db.query(Tables).filter(Tables.floor_id == floor_id).all()
    
    # Mocking generate PDF
    pdf_bytes = b"%PDF-1.4 mock pdf data"
    
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=floor_plan_{floor.name}.pdf"}
    )

@router.post("/tables/print-signs")
async def batch_print_reservation_signs(
    request: BatchPrintSignsRequest,
    db: Session = Depends(get_db),
    restaurant: Restaurant = Depends(get_current_restaurant)
):
    """Generate PDF with multiple reservation signs for printing"""
    
    # Mocking generate PDF
    pdf_bytes = b"%PDF-1.4 mock pdf data for signs"
    
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=reservation_signs.pdf"}
    )

@router.post("/floors/{floor_id}/copy")
async def copy_floor_layout(
    floor_id: str,
    request: CopyFloorRequest,
    db: Session = Depends(get_db),
    restaurant: Restaurant = Depends(get_current_restaurant)
):
    """Copy entire floor layout (tables + elements) to a new floor"""
    
    source_floor = db.query(Floors).filter(Floors.id == floor_id).first()
    
    # Create new floor
    new_floor = Floors(
        restaurant_id=restaurant.id,
        name=request.new_name,
        display_order=request.display_order,
        background_image_url=source_floor.background_image_url,
        width=source_floor.width,
        height=source_floor.height
    )
    db.add(new_floor)
    db.flush()
    
    # Copy tables
    tables = db.query(Tables).filter(Tables.floor_id == floor_id).all()
    for table in tables:
        new_table = Tables(
            restaurant_id=restaurant.id,
            table_number=table.table_number,
            capacity=table.capacity,
            floor_id=new_floor.id,
            pos_x=table.pos_x,
            pos_y=table.pos_y,
            shape=table.shape,
            width=table.width,
            height=table.height
        )
        db.add(new_table)
    
    # Copy elements
    elements = db.query(FloorElements).filter(FloorElements.floor_id == floor_id).all()
    for element in elements:
        new_element = FloorElements(
            floor_id=new_floor.id,
            element_type=element.element_type,
            element_data=element.element_data
        )
        db.add(new_element)
    
    db.commit()
    
    return {"success": True, "new_floor_id": new_floor.id}
