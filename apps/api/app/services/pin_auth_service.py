"""PinAuthService for cashier 4-digit PIN authentication, rate limiting, and session tracking."""
import logging
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.models.staff import Staff
from app.models.session import CashierSession
from app.core.security import create_access_token

logger = logging.getLogger(__name__)

MAX_PIN_ATTEMPTS = 5

class PinAuthService:
    def _hash_pin(self, pin: str) -> str:
        """Hash PIN string using SHA-256 for secure comparison."""
        return hashlib.sha256(pin.encode('utf-8')).hexdigest()

    async def setup_pin(self, db: AsyncSession, user_id: UUID, pin: str) -> bool:
        """Setup initial 4-digit PIN for cashier."""
        staff = await db.get(Staff, user_id)
        if not staff:
            raise ValueError("Staff member not found")

        hashed_pin = self._hash_pin(pin)
        staff.cashier_pin = pin  # store 4-digit PIN (and hashed if needed)
        staff.pin_code = hashed_pin
        staff.pin_set_at = datetime.now(timezone.utc)
        staff.pin_attempts = 0
        staff.pin_locked_at = None

        await db.commit()
        await db.refresh(staff)
        return True

    async def verify_pin(self, db: AsyncSession, user_id: UUID, pin: str) -> bool:
        """Verify cashier 4-digit PIN with attempt tracking and auto-lock."""
        staff = await db.get(Staff, user_id)
        if not staff:
            raise ValueError("Staff member not found")

        if staff.pin_locked_at:
            # Check if lock expired (e.g. 15 minute lock)
            if datetime.now(timezone.utc) - staff.pin_locked_at < timedelta(minutes=15):
                raise ValueError("Account PIN is temporarily locked due to too many failed attempts. Try again in 15 minutes or contact a manager.")
            else:
                staff.pin_locked_at = None
                staff.pin_attempts = 0
                await db.commit()

        target_pin = staff.cashier_pin or staff.pin_code
        hashed_pin = self._hash_pin(pin)

        is_match = False
        if staff.cashier_pin:
            is_match = (staff.cashier_pin == pin) or (staff.cashier_pin == hashed_pin)
        
        if not is_match and staff.pin_code:
            is_match = (staff.pin_code == pin) or (staff.pin_code == hashed_pin)
            if not is_match:
                try:
                    from app.core import security
                    is_match = security.verify_pin(pin, staff.pin_code)
                except Exception:
                    pass

        if not is_match:
            staff.pin_attempts = (staff.pin_attempts or 0) + 1
            if staff.pin_attempts >= MAX_PIN_ATTEMPTS:
                staff.pin_locked_at = datetime.now(timezone.utc)
                await db.commit()
                raise ValueError(f"PIN locked after {MAX_PIN_ATTEMPTS} failed attempts. Please contact a manager.")
            await db.commit()
            return False

        # Reset attempts on success
        staff.pin_attempts = 0
        staff.pin_locked_at = None
        await db.commit()
        return True

    async def change_pin(self, db: AsyncSession, user_id: UUID, current_pin: str, new_pin: str) -> bool:
        """Verify current PIN and update to new PIN."""
        verified = await self.verify_pin(db, user_id, current_pin)
        if not verified:
            raise ValueError("Current PIN is invalid.")
        return await self.setup_pin(db, user_id, new_pin)

    async def reset_pin(self, db: AsyncSession, user_id: UUID, new_pin: str, resetter_id: UUID) -> bool:
        """Reset PIN by manager/owner."""
        resetter = await db.get(Staff, resetter_id)
        if not resetter or resetter.role.value not in ["owner", "admin", "manager"]:
            raise ValueError("Only managers or owners can reset cashier PINs.")

        return await self.setup_pin(db, user_id, new_pin)

    async def create_session(
        self,
        db: AsyncSession,
        user_id: UUID,
        terminal_id: Optional[str] = "Terminal-1",
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> CashierSession:
        """Create new active cashier session and close existing sessions."""
        # Deactivate previous active sessions for user
        stmt = update(CashierSession).where(
            CashierSession.user_id == user_id,
            CashierSession.status == "active"
        ).values(
            status="ended",
            logged_out_at=datetime.now(timezone.utc)
        )
        await db.execute(stmt)

        session = CashierSession(
            user_id=user_id,
            terminal_id=terminal_id,
            status="active",
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)
        return session

    async def get_session(self, db: AsyncSession, session_id: UUID) -> Optional[CashierSession]:
        return await db.get(CashierSession, session_id)

    async def get_active_session(self, db: AsyncSession, user_id: UUID) -> Optional[CashierSession]:
        stmt = select(CashierSession).where(
            CashierSession.user_id == user_id,
            CashierSession.status.in_(["active", "locked"])
        ).order_by(CashierSession.logged_in_at.desc())
        res = await db.execute(stmt)
        return res.scalars().first()

    async def extend_session(self, db: AsyncSession, session_id: UUID) -> CashierSession:
        session = await self.get_session(db, session_id)
        if not session or session.status == "ended":
            raise ValueError("Session is not active")

        session.last_activity_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(session)
        return session

    async def end_session(self, db: AsyncSession, session_id: UUID) -> CashierSession:
        session = await self.get_session(db, session_id)
        if not session:
            raise ValueError("Session not found")

        session.status = "ended"
        session.logged_out_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(session)
        return session

    async def lock_session(self, db: AsyncSession, session_id: UUID) -> CashierSession:
        session = await self.get_session(db, session_id)
        if not session or session.status == "ended":
            raise ValueError("Session is not active")

        session.status = "locked"
        await db.commit()
        await db.refresh(session)
        return session

    async def unlock_session(self, db: AsyncSession, session_id: UUID, pin: str) -> CashierSession:
        session = await self.get_session(db, session_id)
        if not session or session.status == "ended":
            raise ValueError("Session is not active")

        verified = await self.verify_pin(db, session.user_id, pin)
        if not verified:
            raise ValueError("Invalid PIN code")

        session.status = "active"
        session.last_activity_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(session)
        return session

    async def check_session_timeout(self, db: AsyncSession, session_id: UUID, timeout_minutes: int = 30) -> bool:
        session = await self.get_session(db, session_id)
        if not session or session.status != "active":
            return True

        if datetime.now(timezone.utc) - session.last_activity_at > timedelta(minutes=timeout_minutes):
            session.status = "locked"
            await db.commit()
            return True
        return False

pin_auth_service = PinAuthService()
