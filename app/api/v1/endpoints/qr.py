"""QR API router for generating table QR codes, styling, bulk export, and scan tracking."""
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.core.dependencies import require_permission
from app.models.staff import Staff
from app.schemas.qr import (
    QRCodeCreate, QRCodeUpdate, QRCodeResponse, 
    QRDesignRequest, QRDesignResponse, QRDesignData
)
from app.services.qr_service import qr_service

qr_router = APIRouter(prefix="/qr", tags=["qr"])

@qr_router.get("/table/{table_number}", response_model=QRCodeResponse)
async def get_table_qr(
    table_number: str,
    db: AsyncSession = Depends(get_db),
    current_user: Staff = Depends(require_permission("view_links"))
):
    """Get QR code for a specific table."""
    qr_obj = await qr_service.get_table_qr(db, table_number, current_user.restaurant_id)
    if not qr_obj:
        raise HTTPException(status_code=404, detail=f"QR code for table {table_number} not found")
    return qr_obj

@qr_router.post("/generate", response_model=QRCodeResponse, status_code=status.HTTP_201_CREATED)
async def generate_qr(
    data: QRCodeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Staff = Depends(require_permission("manage_links"))
):
    """Generate or update QR code for a table."""
    return await qr_service.generate_table_qr(
        db=db,
        table_number=data.table_number,
        restaurant_id=current_user.restaurant_id,
        branch_id=data.branch_id,
        design=data.qr_data
    )

@qr_router.post("/bulk", response_model=List[QRCodeResponse])
async def bulk_generate_qr(
    payload: QRDesignRequest,
    branch_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: Staff = Depends(require_permission("manage_links"))
):
    """Bulk generate QR codes for a list of table numbers."""
    return await qr_service.bulk_generate_qr(
        db=db,
        table_numbers=payload.table_numbers,
        restaurant_id=current_user.restaurant_id,
        branch_id=branch_id,
        design=payload.design
    )

@qr_router.get("/download-all")
async def download_all_qr_codes(
    db: AsyncSession = Depends(get_db),
    current_user: Staff = Depends(require_permission("manage_links"))
):
    """Download ZIP archive of all generated table QR codes."""
    zip_bytes = await qr_service.download_all_qr_codes(db, current_user.restaurant_id)
    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=PlateLink_QR_Codes_{current_user.restaurant_id}.zip"}
    )

@qr_router.post("/design", response_model=QRDesignResponse)
async def design_qr(
    payload: QRDesignRequest,
    branch_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: Staff = Depends(require_permission("manage_links"))
):
    """Apply custom design branding to table QR codes."""
    qr_list = await qr_service.bulk_generate_qr(
        db=db,
        table_numbers=payload.table_numbers,
        restaurant_id=current_user.restaurant_id,
        branch_id=branch_id,
        design=payload.design
    )
    download_url = f"/api/v1/qr/download-all"
    return QRDesignResponse(qr_codes=qr_list, download_url=download_url)

@qr_router.get("/{id}/analytics")
async def get_qr_analytics(
    id: UUID,
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: Staff = Depends(require_permission("view_links"))
):
    """Get QR code scan & order analytics."""
    return await qr_service.get_qr_analytics(db, id, start_date, end_date)

@qr_router.post("/{id}/track-scan", status_code=status.HTTP_200_OK)
async def track_qr_scan(
    id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Public endpoint to track when a diner scans a table QR code."""
    await qr_service.increment_scan_count(db, id)
    return {"success": True, "message": "Scan recorded"}
