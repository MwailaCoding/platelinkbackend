# app/api/v1/endpoints/tables.py
from typing import List
import qrcode
import io
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from app.core import security
from app.core.deps import get_db, get_current_user, check_role
from app.models import Table, Staff, TableStatus, Restaurant
from app.schemas import schemas
from app.services.cloudinary import CloudinaryService
from app.websockets.manager import manager
from app.services.qr_pdf_generator import QRPDFGenerator
from app.utils.qr_utils import generate_qr_token


router = APIRouter()

@router.get("/", response_model=List[schemas.TableRead])
async def list_tables(current_user: Staff = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    stmt = select(Table).where(Table.restaurant_id == current_user.restaurant_id)
    result = await db.execute(stmt)
    return result.scalars().all()

async def generate_table_qr_img(restaurant_id: str, restaurant_slug: str, table_id: str, table_number: int):
    from datetime import timedelta
    token = security.create_access_token(
        subject=str(table_id),
        expires_delta=timedelta(days=3650),
        extra_claims={"type": "table", "restaurant_id": str(restaurant_id), "table_number": table_number}
    )
    qr = qrcode.QRCode(
        version=4,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=5
    )
    qr.add_data(f"https://platelink-customer.vercel.app/{restaurant_slug}/menu/{token}")
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    return token, img

@router.post("/bulk-create")
async def bulk_create_tables(data: schemas.TableBulkCreate, current_user: Staff = Depends(check_role(["owner", "manager"])), db: AsyncSession = Depends(get_db)):
    rest = await db.get(Restaurant, current_user.restaurant_id)
    restaurant_slug = rest.slug if rest else "restaurant"
    for num in range(data.start_number, data.end_number + 1):
        stmt = select(Table).where(Table.restaurant_id == current_user.restaurant_id, Table.table_number == num)
        if (await db.execute(stmt)).scalar(): continue
        new_table = Table(restaurant_id=current_user.restaurant_id, table_number=num, capacity=data.capacity, location=data.location, status=TableStatus.available)
        db.add(new_table); await db.flush()
        token, img = await generate_table_qr_img(current_user.restaurant_id, restaurant_slug, new_table.id, num)
        buf = io.BytesIO(); img.save(buf, format="PNG")
        url = await CloudinaryService.upload_image(buf.getvalue(), folder="qr_codes")
        new_table.qr_code_token = token
        new_table.qr_code_url = url
    await db.commit(); return {"msg": "Tables created"}

@router.get("/qr-codes/download")
async def download_qr_codes(
    format: str = "pdf",
    current_user: Staff = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Table).where(Table.restaurant_id == current_user.restaurant_id).order_by(Table.table_number.asc())
    tables = (await db.execute(stmt)).scalars().all()
    rest = await db.get(Restaurant, current_user.restaurant_id)
    
    if not rest:
        raise HTTPException(status_code=404, detail="Restaurant not found")
        
    table_dicts = []
    has_new_tokens = False
    
    for t in tables:
        token = t.qr_code_token
        if not token:
            token = generate_qr_token(t.id, current_user.restaurant_id)
            t.qr_code_token = token
            db.add(t)
            has_new_tokens = True
            
        table_dicts.append({
            "number": t.table_number,
            "token": token
        })
        
    if has_new_tokens:
        await db.commit()
        
    generator = QRPDFGenerator(restaurant_name=rest.name, restaurant_slug=rest.slug)
    pdf_bytes = generator.generate_pdf(table_dicts)
    
    buffer = io.BytesIO(pdf_bytes)
    filename = f"{rest.slug}_qr_codes.pdf"
    
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )

from uuid import UUID
from datetime import datetime, timezone

@router.patch("/{table_id}/status", response_model=schemas.TableRead)
async def update_table_status(
    table_id: UUID,
    status_update: schemas.TableStatusUpdate,
    current_user: Staff = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    table = await db.get(Table, table_id)
    if not table or table.restaurant_id != current_user.restaurant_id:
        raise HTTPException(status_code=404, detail="Table not found")
        
    old_status = table.status
    new_status = status_update.status
    
    if old_status != new_status:
        table.status = new_status
        table.last_status_change = datetime.now(timezone.utc)
        
        history = list(table.status_history) if table.status_history else []
        history.append({
            "from": old_status.value,
            "to": new_status.value,
            "at": datetime.now(timezone.utc).isoformat(),
            "staff_id": str(current_user.id)
        })
        table.status_history = history
        
        if new_status == TableStatus.occupied and old_status == TableStatus.available:
            table.occupied_since = datetime.now(timezone.utc)
        elif new_status == TableStatus.available:
            table.occupied_since = None
            table.current_session_id = None
            
        await db.commit()
        await db.refresh(table)
        
        await manager.broadcast_to_room(
            f"{table.restaurant_id}_waiter",
            {
                "type": "table_status_updated",
                "data": {
                    "table_id": str(table.id),
                    "table_number": table.table_number,
                    "status": table.status.value
                }
            }
        )
        
    return table
