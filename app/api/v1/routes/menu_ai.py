# app/api/v1/routes/menu_ai.py
import logging
import time
from typing import List, Optional
from decimal import Decimal
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.deps import get_db, check_role
from app.models import Category, MenuItem, Staff, ActivityLog
from app.services.openai_menu_extractor import OpenAIMenuExtractor

logger = logging.getLogger("uvicorn.error")

router = APIRouter()
extractor = OpenAIMenuExtractor()

# Maximum file size (20MB)
MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024

# Pydantic Schemas for Request/Response
class MenuItemConfirm(BaseModel):
    name: str = Field(..., description="Name of the menu item")
    price: Decimal = Field(..., description="Price of the item, must be non-negative")
    description: Optional[str] = Field(None, description="Optional description of the menu item")

class CategoryConfirm(BaseModel):
    name: str = Field(..., description="Name of the category")
    items: List[MenuItemConfirm] = Field(..., description="List of menu items in this category")

class MenuConfirmRequest(BaseModel):
    categories: List[CategoryConfirm] = Field(..., description="List of categories to save")

@router.post("/ai-extract")
async def ai_extract_menu(
    file: UploadFile = File(...),
    current_user: Staff = Depends(check_role(["owner", "manager"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload a menu file (JPEG, PNG, PDF) and extract categories, items, prices, and descriptions.
    Max file size: 20MB.
    """
    # 1. Validate file size
    # Read up to MAX_FILE_SIZE_BYTES + 1 to detect overflow without buffering full huge files
    content = await file.read(MAX_FILE_SIZE_BYTES + 1)
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File is too large. Maximum allowed size is 20MB."
        )
    
    # Reset file cursor for further reading if needed (in our case we already read the content bytes)
    file_bytes = content

    # 2. Validate MIME type
    mime_type = file.content_type
    allowed_types = ["image/jpeg", "image/png", "application/pdf"]
    if mime_type not in allowed_types:
        # Check by extension fallback if mimetype is blank or generic
        filename_lower = file.filename.lower()
        if filename_lower.endswith(".pdf"):
            mime_type = "application/pdf"
        elif filename_lower.endswith((".jpg", ".jpeg")):
            mime_type = "image/jpeg"
        elif filename_lower.endswith(".png"):
            mime_type = "image/png"
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type: {file.content_type or 'unknown'}. Allowed types: JPEG, PNG, PDF."
            )

    start_time = time.time()
    logger.info(f"Starting AI menu extraction for restaurant {current_user.restaurant_id}, file: {file.filename}")

    # 3. Call the appropriate extraction method
    try:
        if mime_type == "application/pdf":
            result = await extractor.extract_from_pdf(file_bytes)
        else:
            result = await extractor.extract_from_image(file_bytes, file.filename)
    except Exception as e:
        logger.error(f"Error during AI extraction: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to extract menu. Technical error: {str(e)}"
        )

    if not result.get("success"):
        logger.error(f"AI extraction unsuccessful: {result.get('error')}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=result.get("error", "AI Extraction failed.")
        )

    # Log completion info
    duration_ms = int((time.time() - start_time) * 1000)
    logger.info(f"AI menu extraction completed successfully in {duration_ms}ms")

    return {
        "success": True,
        "data": result.get("data"),
        "usage": result.get("usage"),
        "processing_time_ms": result.get("processing_time_ms", duration_ms)
    }

@router.post("/ai-extract/confirm")
async def ai_extract_confirm(
    payload: MenuConfirmRequest,
    current_user: Staff = Depends(check_role(["owner", "manager"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Accepts user-edited/confirmed menu categories and items.
    Saves everything atomically within a single database transaction.
    """
    restaurant_id = current_user.restaurant_id

    try:
        # Process everything inside a transaction block
        async with db.begin_nested():
            for cat_data in payload.categories:
                cat_name = cat_data.name.strip()
                if not cat_name:
                    continue

                # Look up existing active category for this restaurant (case-insensitive check)
                stmt = select(Category).where(
                    Category.restaurant_id == restaurant_id,
                    Category.name.ilike(cat_name),
                    Category.is_active == True
                )
                res = await db.execute(stmt)
                category = res.scalar_one_or_none()

                if not category:
                    # Create new category
                    category = Category(
                        restaurant_id=restaurant_id,
                        name=cat_name,
                        display_order=0
                    )
                    db.add(category)
                    await db.flush() # Populate category.id

                # Save items in this category
                for item_data in cat_data.items:
                    item_name = item_data.name.strip()
                    if not item_name:
                        continue
                    
                    if item_data.price < 0:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Price for item '{item_name}' cannot be negative."
                        )

                    new_item = MenuItem(
                        restaurant_id=restaurant_id,
                        category_id=category.id,
                        name=item_name,
                        price=item_data.price,
                        description=item_data.description,
                        is_available=True
                    )
                    db.add(new_item)

            # Log audit activity
            db.add(ActivityLog(
                restaurant_id=restaurant_id,
                staff_id=current_user.id,
                action="ai_menu_extraction_confirmed",
                metadata_info={"categories_count": len(payload.categories)}
            ))

        # Commit external transaction
        await db.commit()
        return {"success": True, "message": "Menu saved successfully"}

    except HTTPException as http_err:
        await db.rollback()
        raise http_err
    except Exception as e:
        await db.rollback()
        logger.error(f"Error saving confirmed AI menu: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save menu changes. Error: {str(e)}"
        )

@router.get("/ai-extract/status/{job_id}")
async def ai_extract_status(
    job_id: str,
    current_user: Staff = Depends(check_role(["owner", "manager"]))
):
    """
    Job status endpoint for long running queries.
    Since vision extraction runs synchronously inside POST request, we return a completed status.
    """
    return {
        "success": True,
        "job_id": job_id,
        "status": "completed",
        "progress": 100,
        "message": "AI extraction is complete."
    }
