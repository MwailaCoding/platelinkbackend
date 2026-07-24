"""QR code generation and validation API endpoints."""
import logging
from uuid import UUID
from typing import Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.core.database import get_db
from apps.api.app.core.permissions import require_permission
from apps.api.app.models.user import User
from apps.api.app.services.qr_service import QRService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/qr", tags=["QR Code"])

@router.post("/staff-qr", response_model=Dict[str, Any])
async def generate_staff_qr(
    current_user: User = Depends(require_permission("view_staff")),
    db: AsyncSession = Depends(get_db)
):
    """Generate QR code payload and image for staff login."""
    service = QRService(db)
    return await service.generate_staff_qr(current_user.id, current_user.restaurant_id)

@router.post("/validate-qr", response_model=Dict[str, Any])
async def validate_staff_qr(
    qr_token: str,
    db: AsyncSession = Depends(get_db)
):
    """Validate a staff login QR code token."""
    service = QRService(db)
    result = await service.validate_staff_qr(qr_token)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired QR token"
        )
    return result

@router.post("/table-qr", response_model=Dict[str, Any])
async def generate_table_qr(
    table_number: int,
    branch_id: Optional[UUID] = None,
    current_user: User = Depends(require_permission("view_settings")),
    db: AsyncSession = Depends(get_db)
):
    """Generate table QR code for customer ordering."""
    service = QRService(db)
    return await service.generate_table_qr(current_user.restaurant_id, table_number, branch_id)
