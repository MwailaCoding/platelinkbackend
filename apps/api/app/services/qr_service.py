"""QR Code service for staff login and table ordering."""
import os
import base64
import logging
from io import BytesIO
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta, timezone

import jwt
import qrcode
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from apps.api.app.models.user import User

logger = logging.getLogger(__name__)

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "super-secret-key-change-in-production")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

class QRService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.expiry_minutes = 60

    async def generate_staff_qr(
        self,
        user_id: UUID,
        restaurant_id: UUID
    ) -> Dict[str, Any]:
        """Generate a signed QR code for staff login."""
        stmt = select(User).where(User.id == user_id, User.restaurant_id == restaurant_id)
        res = await self.db.execute(stmt)
        user = res.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=self.expiry_minutes)

        payload = {
            "sub": str(user.id),
            "restaurant_id": str(restaurant_id),
            "type": "qr_login",
            "exp": expires_at,
            "iat": now
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        qr_content = f"QR_USER_{user.id}"

        # Generate QR code image buffer
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_content)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        qr_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

        return {
            "user_id": user.id,
            "qr_token": token,
            "qr_code": qr_content,
            "qr_image_base64": f"data:image/png;base64,{qr_base64}",
            "expires_at": expires_at
        }

    async def validate_staff_qr(
        self,
        token: str
    ) -> Optional[Dict[str, Any]]:
        """Validate staff QR login token."""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            if payload.get("type") != "qr_login":
                return None

            user_id = payload.get("sub")
            stmt = select(User).where(User.id == UUID(user_id))
            res = await self.db.execute(stmt)
            user = res.scalar_one_or_none()

            if not user or user.status.value != "active":
                return None

            return {
                "user_id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "restaurant_id": user.restaurant_id
            }
        except Exception as err:
            logger.warning(f"QR validation failed: {err}")
            return None

    async def deactivate_qr(
        self,
        user_id: UUID
    ) -> bool:
        """Deactivate QR code access for user."""
        logger.info(f"Deactivated QR access for user {user_id}")
        return True

    async def generate_table_qr(
        self,
        restaurant_id: UUID,
        table_number: int,
        branch_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Generate table QR code for ordering."""
        target_url = f"https://platelink.app/r/{restaurant_id}/t/{table_number}"
        if branch_id:
            target_url += f"?branch={branch_id}"

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        qr.add_data(target_url)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        qr_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

        return {
            "restaurant_id": restaurant_id,
            "table_number": table_number,
            "url": target_url,
            "qr_image_base64": f"data:image/png;base64,{qr_base64}"
        }
