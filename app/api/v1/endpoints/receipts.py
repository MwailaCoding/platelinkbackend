"""Receipt endpoints for digital receipting and printing."""
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.core.dependencies import require_permission
from app.models.staff import Staff
from app.schemas.cashier import DigitalReceiptRequest, DigitalReceiptResponse
from app.services.receipt_service import receipt_service

router = APIRouter(prefix="/receipts", tags=["receipts"])

@router.post("/{order_id}/digital", response_model=DigitalReceiptResponse)
async def send_digital_receipt(
    order_id: UUID,
    request: DigitalReceiptRequest,
    current_user: Staff = Depends(require_permission("view_receipts")),
    db: AsyncSession = Depends(get_db)
):
    """Send digital receipt via WhatsApp/SMS/Email/Print."""
    try:
        receipt = await receipt_service.send_digital_receipt(
            db,
            order_id=order_id,
            channel=request.channel.value if hasattr(request.channel, 'value') else request.channel,
            recipient=request.recipient,
            cashier_id=current_user.id,
            message=request.message
        )
        return receipt
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{order_id}", response_model=List[DigitalReceiptResponse])
async def get_order_receipts(
    order_id: UUID,
    current_user: Staff = Depends(require_permission("view_receipts")),
    db: AsyncSession = Depends(get_db)
):
    """Get all receipts sent for an order."""
    receipts = await receipt_service.get_receipts_by_order(db, order_id)
    return receipts

@router.get("/receipt/{receipt_id}", response_model=DigitalReceiptResponse)
async def get_receipt_details(
    receipt_id: UUID,
    current_user: Staff = Depends(require_permission("view_receipts")),
    db: AsyncSession = Depends(get_db)
):
    """Get single receipt details by receipt_id."""
    receipt = await receipt_service.get_receipt(db, receipt_id)
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")
    return receipt
