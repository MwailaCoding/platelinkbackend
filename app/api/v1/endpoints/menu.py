# app/api/v1/endpoints/menu.py
from typing import List, Optional
import csv
import io
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, Body
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.core.deps import get_db, get_current_user, check_role
from app.models import Category, MenuItem, MenuItemModifier, Staff, ActivityLog
from app.schemas import schemas
from app.websockets.manager import manager
from app.services.cloudinary import CloudinaryService

router = APIRouter()

# --- Categories ---

@router.get("/categories", response_model=List[schemas.CategoryRead])
async def list_categories(
    current_user: Staff = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all menu categories.
    """
    stmt = select(Category).where(
        Category.restaurant_id == current_user.restaurant_id,
        Category.is_active == True
    ).order_by(Category.display_order.asc())
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/categories", response_model=schemas.CategoryRead)
async def create_category(
    data: schemas.CategoryCreate,
    current_user: Staff = Depends(check_role(["owner", "manager"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new category.
    """
    new_cat = Category(
        restaurant_id=current_user.restaurant_id,
        name=data.name,
        display_order=data.display_order
    )
    db.add(new_cat)
    await db.commit()
    await db.refresh(new_cat)
    return new_cat

@router.put("/categories/{cat_id}", response_model=schemas.CategoryRead)
async def update_category(
    cat_id: str,
    data: schemas.CategoryCreate,
    current_user: Staff = Depends(check_role(["owner", "manager"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a category.
    """
    cat = await db.get(Category, cat_id)
    if not cat or cat.restaurant_id != current_user.restaurant_id:
        raise HTTPException(status_code=404, detail="Category not found")
        
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(cat, field, value)
        
    await db.commit()
    await db.refresh(cat)
    return cat

@router.delete("/categories/{cat_id}")
async def delete_category(
    cat_id: str,
    current_user: Staff = Depends(check_role(["owner", "manager"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a category if empty.
    """
    cat = await db.get(Category, cat_id)
    if not cat or cat.restaurant_id != current_user.restaurant_id:
        raise HTTPException(status_code=404, detail="Category not found")
        
    # Check if items exist
    stmt = select(MenuItem).where(MenuItem.category_id == cat_id)
    result = await db.execute(stmt)
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Cannot delete category with items. Reassign them first.")
        
    await db.delete(cat)
    await db.commit()
    return {"msg": "Category deleted"}

# --- Menu Items ---

@router.get("/items", response_model=List[schemas.MenuItemRead])
async def list_items(
    category_id: Optional[str] = None,
    is_available: Optional[bool] = None,
    current_user: Staff = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List menu items with filtering.
    """
    stmt = select(MenuItem).where(MenuItem.restaurant_id == current_user.restaurant_id)
    if category_id:
        stmt = stmt.where(MenuItem.category_id == category_id)
    if is_available is not None:
        stmt = stmt.where(MenuItem.is_available == is_available)
        
    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/items/{item_id}", response_model=schemas.MenuItemRead)
async def get_item_detail(
    item_id: str,
    current_user: Staff = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get menu item detail with modifiers.
    """
    item = await db.get(MenuItem, item_id)
    if not item or item.restaurant_id != current_user.restaurant_id:
        raise HTTPException(status_code=404, detail="Item not found")
        
    # Fetch modifiers
    stmt = select(MenuItemModifier).where(MenuItemModifier.menu_item_id == item_id)
    res = await db.execute(stmt)
    item.modifiers = res.scalars().all()
    return item

@router.post("/items", response_model=schemas.MenuItemRead)
async def create_item(
    data: schemas.MenuItemCreate,
    current_user: Staff = Depends(check_role(["owner", "manager"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new menu item.
    """
    if data.price < 0:
        raise HTTPException(status_code=400, detail="Price cannot be negative")
        
    new_item = MenuItem(
        restaurant_id=current_user.restaurant_id,
        **data.model_dump()
    )
    db.add(new_item)
    db.add(ActivityLog(
        restaurant_id=current_user.restaurant_id,
        staff_id=current_user.id,
        action=f"created_item_{data.name}"
    ))
    await db.commit()
    await db.refresh(new_item)
    new_item.modifiers = []
    return new_item

@router.put("/items/{item_id}", response_model=schemas.MenuItemRead)
async def update_item(
    item_id: str,
    data: schemas.MenuItemCreate,
    current_user: Staff = Depends(check_role(["owner", "manager"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a menu item.
    """
    item = await db.get(MenuItem, item_id)
    if not item or item.restaurant_id != current_user.restaurant_id:
        raise HTTPException(status_code=404, detail="Item not found")
        
    old_price = item.price
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
        
    if old_price != item.price:
        db.add(ActivityLog(
            restaurant_id=current_user.restaurant_id,
            staff_id=current_user.id,
            action=f"price_changed_{item_id}",
            metadata_info={"old": float(old_price), "new": float(item.price)}
        ))
        
    await db.commit()
    await db.refresh(item)
    return item

@router.delete("/items/{item_id}")
async def delete_item(
    item_id: str,
    current_user: Staff = Depends(check_role(["owner", "manager"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Soft delete menu item.
    """
    item = await db.get(MenuItem, item_id)
    if not item or item.restaurant_id != current_user.restaurant_id:
        raise HTTPException(status_code=404, detail="Item not found")
        
    item.is_available = False
    await db.commit()
    return {"msg": "Item marked as unavailable"}

@router.post("/items/upload-image")
async def upload_menu_item_image(
    file: UploadFile = File(...),
    current_user: Staff = Depends(check_role(["owner", "manager"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload menu item image to Cloudinary.
    """
    if file.content_type not in ["image/jpeg", "image/png", "image/webp"]:
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 5MB)")
        
    url = await CloudinaryService.upload_image(content)
    return {"url": url}

@router.post("/items/bulk-import")
async def bulk_import_items(
    file: UploadFile = File(...),
    current_user: Staff = Depends(check_role(["owner", "manager"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Bulk import items from CSV.
    """
    content = await file.read()
    decoded = content.decode("utf-8")
    reader = csv.DictReader(io.StringIO(decoded))
    
    created = 0
    errors = []
    
    for row in reader:
        try:
            # Find or create category
            cat_stmt = select(Category).where(
                Category.restaurant_id == current_user.restaurant_id,
                Category.name == row['category']
            )
            cat_res = await db.execute(cat_stmt)
            cat = cat_res.scalar_one_or_none()
            if not cat:
                cat = Category(restaurant_id=current_user.restaurant_id, name=row['category'])
                db.add(cat)
                await db.flush()
            
            # Validate preparation_time
            prep_time_str = row.get('preparation_time')
            if not prep_time_str or not prep_time_str.strip():
                raise ValueError("Preparation time is required")
            try:
                prep_time = int(prep_time_str)
                if prep_time <= 0 or prep_time > 180:
                    raise ValueError("Preparation time must be between 1 and 180 minutes")
            except ValueError:
                raise ValueError("Preparation time must be a positive integer")

            new_item = MenuItem(
                restaurant_id=current_user.restaurant_id,
                category_id=cat.id,
                name=row['name'],
                price=float(row['price']),
                description=row.get('description'),
                preparation_time=prep_time,
                is_available=True
            )
            db.add(new_item)
            created += 1
        except Exception as e:
            errors.append(f"Row {row.get('name', 'Unknown')}: {str(e)}")
            
    await db.commit()
    return {"created": created, "errors": errors}

@router.put("/items/{item_id}/toggle-availability")
async def toggle_availability(
    item_id: str,
    current_user: Staff = Depends(check_role(["owner", "manager", "chef"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Quick toggle for item availability.
    """
    item = await db.get(MenuItem, item_id)
    if not item or item.restaurant_id != current_user.restaurant_id:
        raise HTTPException(status_code=404, detail="Item not found")
        
    item.is_available = not item.is_available
    if not item.is_available:
        item.stock_quantity = 0
        
    # Broadcast to all customer sessions
    await manager.broadcast(
        {"type": "item_availability", "item_id": str(item.id), "is_available": item.is_available},
        f"session_{current_user.restaurant_id}" # Simplified room naming
    )
    
    await db.commit()
    return {"is_available": item.is_available}

# --- Modifiers ---

@router.get("/items/{item_id}/modifiers", response_model=List[schemas.ModifierRead])
async def list_modifiers(
    item_id: str,
    current_user: Staff = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List modifiers for an item.
    """
    stmt = select(MenuItemModifier).where(MenuItemModifier.menu_item_id == item_id)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/items/{item_id}/modifiers", response_model=schemas.ModifierRead)
async def create_modifier(
    item_id: str,
    data: schemas.ModifierCreate,
    current_user: Staff = Depends(check_role(["owner", "manager"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Add a modifier to an item.
    """
    new_mod = MenuItemModifier(
        restaurant_id=current_user.restaurant_id,
        menu_item_id=item_id,
        **data.model_dump()
    )
    db.add(new_mod)
    await db.commit()
    await db.refresh(new_mod)
    return new_mod

@router.delete("/modifiers/{mod_id}")
async def delete_modifier(
    mod_id: str,
    current_user: Staff = Depends(check_role(["owner", "manager"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a modifier.
    """
    mod = await db.get(MenuItemModifier, mod_id)
    if not mod or mod.restaurant_id != current_user.restaurant_id:
        raise HTTPException(status_code=404, detail="Modifier not found")
        
    await db.delete(mod)
    await db.commit()
    return {"msg": "Modifier deleted"}

@router.put("/modifiers/{mod_id}", response_model=schemas.ModifierRead)
async def update_modifier(
    mod_id: str,
    data: schemas.ModifierCreate,
    current_user: Staff = Depends(check_role(["owner", "manager"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Update an existing modifier.
    """
    mod = await db.get(MenuItemModifier, mod_id)
    if not mod or mod.restaurant_id != current_user.restaurant_id:
        raise HTTPException(status_code=404, detail="Modifier not found")
        
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(mod, field, value)
        
    await db.commit()
    await db.refresh(mod)
    return mod

@router.get("/items/export")
async def export_menu_items(
    current_user: Staff = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Export menu items as a CSV file.
    """
    stmt = select(MenuItem).where(MenuItem.restaurant_id == current_user.restaurant_id)
    result = await db.execute(stmt)
    items = result.scalars().all()
    
    # Generate CSV content
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow(["id", "name", "price", "description", "category_id", "is_available"])
    
    # Rows
    for item in items:
        writer.writerow([
            str(item.id),
            item.name,
            float(item.price),
            item.description or "",
            str(item.category_id),
            "TRUE" if item.is_available else "FALSE"
        ])
        
    output.seek(0)
    
    headers = {
        'Content-Disposition': 'attachment; filename="menu_items.csv"'
    }
    return StreamingResponse(io.BytesIO(output.getvalue().encode("utf-8")), media_type="text/csv", headers=headers)

@router.post("/categories/reorder")
async def reorder_categories(
    category_ids: List[str] = Body(..., embed=True),
    current_user: Staff = Depends(check_role(["owner", "manager"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Reorder menu categories.
    """
    for index, cat_id in enumerate(category_ids):
        stmt = update(Category).where(
            Category.id == cat_id,
            Category.restaurant_id == current_user.restaurant_id
        ).values(display_order=index)
        await db.execute(stmt)
        
    await db.commit()
    return {"msg": "Categories reordered successfully"}
