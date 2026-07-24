"""Staff invitation API endpoints."""
import logging
from uuid import UUID
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.core.database import get_db
from apps.api.app.core.permissions import require_permission
from apps.api.app.models.user import User
from apps.api.app.services.invitation_service import InvitationService
from apps.api.app.schemas.invitation import (
    StaffInviteCreate,
    StaffInviteResponse,
    AcceptInvitationRequest,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/invitations", tags=["Invitations"])

@router.post("/", response_model=StaffInviteResponse, status_code=status.HTTP_201_CREATED)
async def create_invitation(
    invite_data: StaffInviteCreate,
    current_user: User = Depends(require_permission("add_staff")),
    db: AsyncSession = Depends(get_db)
):
    """Create and send staff invitation email/SMS."""
    service = InvitationService(db)
    invitation = await service.create_invitation(
        email=invite_data.email,
        restaurant_id=current_user.restaurant_id,
        role_id=invite_data.role_id,
        invited_by=current_user.id,
        first_name=invite_data.first_name,
        last_name=invite_data.last_name,
        pin=invite_data.pin,
        message=invite_data.message,
        branch_id=invite_data.branch_id,
        phone=invite_data.phone
    )
    return StaffInviteResponse.model_validate(invitation)

@router.get("/", response_model=List[StaffInviteResponse])
async def list_invitations(
    inv_status: Optional[str] = Query(None, alias="status"),
    current_user: User = Depends(require_permission("view_staff")),
    db: AsyncSession = Depends(get_db)
):
    """List all invitations for current restaurant."""
    service = InvitationService(db)
    invitations = await service.list_invitations(current_user.restaurant_id, inv_status)
    return [StaffInviteResponse.model_validate(i) for i in invitations]

@router.post("/accept", response_model=Dict[str, Any])
async def accept_invitation(
    token: str = Query(...),
    accept_data: AcceptInvitationRequest = None,
    db: AsyncSession = Depends(get_db)
):
    """Accept staff invitation token and complete account setup."""
    service = InvitationService(db)
    data = accept_data.model_dump() if accept_data else {}
    return await service.accept_invitation(token, data)

@router.post("/{invitation_id}/resend", response_model=StaffInviteResponse)
async def resend_invitation(
    invitation_id: UUID,
    current_user: User = Depends(require_permission("add_staff")),
    db: AsyncSession = Depends(get_db)
):
    """Resend staff invitation with a new token."""
    service = InvitationService(db)
    invitation = await service.resend_invitation(invitation_id)
    return StaffInviteResponse.model_validate(invitation)

@router.delete("/{invitation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_invitation(
    invitation_id: UUID,
    current_user: User = Depends(require_permission("add_staff")),
    db: AsyncSession = Depends(get_db)
):
    """Cancel pending staff invitation."""
    service = InvitationService(db)
    success = await service.cancel_invitation(invitation_id, current_user.restaurant_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found")
    return None
