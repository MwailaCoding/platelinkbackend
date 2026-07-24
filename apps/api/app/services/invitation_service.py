"""Staff invitation business logic service."""
import secrets
import logging
from uuid import UUID
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from apps.api.app.models.invitation import StaffInvitation
from apps.api.app.models.user import User
from apps.api.app.models.staff import Staff
from apps.api.app.models.role import Role
from apps.api.app.models.restaurant import Restaurant
from apps.api.app.models.enums import UserStatus
from apps.api.app.core.auth import hash_password
from apps.api.app.core.email import send_invitation_email
from apps.api.app.core.sms import send_invitation_sms

logger = logging.getLogger(__name__)

class InvitationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.expiry_days = 7

    async def create_invitation(
        self,
        email: str,
        restaurant_id: UUID,
        role_id: UUID,
        invited_by: UUID,
        first_name: str,
        last_name: str,
        pin: str,
        message: Optional[str] = None,
        branch_id: Optional[UUID] = None,
        phone: Optional[str] = None
    ) -> StaffInvitation:
        """Create and send staff invitation."""
        email_clean = email.lower().strip()

        # Check existing active user
        stmt = select(User).where(User.email == email_clean)
        res = await self.db.execute(stmt)
        if res.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )

        # Check restaurant & role
        rest_stmt = select(Restaurant).where(Restaurant.id == restaurant_id)
        rest_res = await self.db.execute(rest_stmt)
        restaurant = rest_res.scalar_one_or_none()
        if not restaurant:
            raise HTTPException(status_code=404, detail="Restaurant not found")

        role_stmt = select(Role).where(Role.id == role_id)
        role_res = await self.db.execute(role_stmt)
        role = role_res.scalar_one_or_none()
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")

        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(days=self.expiry_days)

        invitation = StaffInvitation(
            email=email_clean,
            restaurant_id=restaurant_id,
            role_id=role_id,
            branch_id=branch_id,
            invited_by=invited_by,
            token=token,
            expires_at=expires_at,
            status="pending",
            message=message
        )
        self.db.add(invitation)
        await self.db.commit()
        await self.db.refresh(invitation)

        # Send notifications
        invite_url = f"http://localhost:3000/accept-invite?token={token}"
        await send_invitation_email(
            to=email_clean,
            first_name=first_name,
            last_name=last_name,
            restaurant_name=restaurant.name,
            role_name=role.name,
            invite_url=invite_url,
            pin=pin
        )

        if phone:
            await send_invitation_sms(
                to=phone,
                first_name=first_name,
                restaurant_name=restaurant.name,
                pin=pin
            )

        return invitation

    async def accept_invitation(
        self,
        token: str,
        user_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Accept staff invitation and activate user account."""
        invitation = await self.get_invitation(token)
        if not invitation:
            raise HTTPException(status_code=404, detail="Invitation token not found")

        if invitation.status != "pending":
            raise HTTPException(status_code=400, detail=f"Invitation is already {invitation.status}")

        if datetime.now(timezone.utc) > invitation.expires_at.replace(tzinfo=timezone.utc):
            invitation.status = "expired"
            await self.db.commit()
            raise HTTPException(status_code=400, detail="Invitation has expired")

        # Create user
        raw_password = user_data.get("password") or "DefaultSecurePass123!"
        hashed_pass = hash_password(raw_password)

        new_user = User(
            email=invitation.email,
            phone=user_data.get("phone"),
            password_hash=hashed_pass,
            first_name=user_data.get("first_name", "Staff"),
            last_name=user_data.get("last_name", "Member"),
            role_id=invitation.role_id,
            restaurant_id=invitation.restaurant_id,
            branch_id=invitation.branch_id,
            pin=user_data.get("pin", "1234"),
            status=UserStatus.ACTIVE
        )
        self.db.add(new_user)
        await self.db.flush()

        new_staff = Staff(
            user_id=new_user.id,
            employee_id=f"EMP-{new_user.id.hex[:6].upper()}",
            department=user_data.get("department", "General"),
            position=user_data.get("position", "Staff"),
            hire_date=datetime.now(timezone.utc).date()
        )
        self.db.add(new_staff)

        invitation.status = "accepted"
        invitation.accepted_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(new_user)
        await self.db.refresh(new_staff)

        return {
            "message": "Invitation accepted successfully",
            "user_id": new_user.id,
            "staff_id": new_staff.id,
            "email": new_user.email,
            "status": "active"
        }

    async def get_invitation(
        self,
        token: str
    ) -> Optional[StaffInvitation]:
        """Get invitation by token."""
        stmt = select(StaffInvitation).where(StaffInvitation.token == token)
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def resend_invitation(
        self,
        invitation_id: UUID
    ) -> StaffInvitation:
        """Regenerate token and resend invitation."""
        stmt = select(StaffInvitation).where(StaffInvitation.id == invitation_id)
        res = await self.db.execute(stmt)
        invitation = res.scalar_one_or_none()
        if not invitation:
            raise HTTPException(status_code=404, detail="Invitation not found")

        invitation.token = secrets.token_urlsafe(32)
        invitation.expires_at = datetime.now(timezone.utc) + timedelta(days=self.expiry_days)
        invitation.status = "pending"
        await self.db.commit()
        await self.db.refresh(invitation)

        invite_url = f"http://localhost:3000/accept-invite?token={invitation.token}"
        await send_invitation_email(
            to=invitation.email,
            first_name="Staff",
            last_name="Member",
            restaurant_name="Restaurant",
            role_name="Role",
            invite_url=invite_url,
            pin="1234"
        )
        return invitation

    async def cancel_invitation(
        self,
        invitation_id: UUID,
        restaurant_id: UUID
    ) -> bool:
        """Cancel pending invitation."""
        stmt = select(StaffInvitation).where(
            StaffInvitation.id == invitation_id,
            StaffInvitation.restaurant_id == restaurant_id
        )
        res = await self.db.execute(stmt)
        invitation = res.scalar_one_or_none()
        if not invitation:
            return False

        invitation.status = "cancelled"
        await self.db.commit()
        return True

    async def list_invitations(
        self,
        restaurant_id: UUID,
        inv_status: Optional[str] = None
    ) -> List[StaffInvitation]:
        """List all invitations for a restaurant."""
        stmt = select(StaffInvitation).where(StaffInvitation.restaurant_id == restaurant_id)
        if inv_status:
            stmt = stmt.where(StaffInvitation.status == inv_status)
        stmt = stmt.order_by(StaffInvitation.created_at.desc())
        res = await self.db.execute(stmt)
        return res.scalars().all()
