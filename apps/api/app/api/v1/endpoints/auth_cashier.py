"""FastAPI router for Cashier 4-digit PIN authentication & POS session management."""
import logging
from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, get_current_user
from app.core.dependencies import require_permission
from app.core.security import create_access_token
from app.models.staff import Staff
from app.models.restaurant import Restaurant
from app.models.enums import StaffRole
from app.schemas.cashier_auth import (
    PinLoginRequest, PinSetupRequest, PinChangeRequest, PinResetRequest,
    PinVerifyRequest, PinLoginResponse, SessionResponse, LogoutRequest,
    ExtendSessionRequest, LockSessionRequest, UnlockSessionRequest
)
from app.services.pin_auth_service import pin_auth_service

logger = logging.getLogger(__name__)

from pydantic import BaseModel
from typing import List

class CashierOption(BaseModel):
    id: UUID
    full_name: str
    role: str
    has_pin: bool

router = APIRouter(prefix="/auth/cashier", tags=["cashier-auth"])

@router.get("/list", response_model=List[CashierOption])
async def list_cashiers(
    db: AsyncSession = Depends(get_db)
):
    """List active cashier staff members for quick terminal landing PIN selection."""
    stmt = select(Staff).where(Staff.is_active != False)
    res = await db.execute(stmt)
    staff_members = res.scalars().all()

    if not staff_members:
        # Auto-create default cashier staff if database has no staff entries yet
        stmt_r = select(Restaurant).limit(1)
        res_r = await db.execute(stmt_r)
        rest = res_r.scalars().first()
        if rest:
            new_staff = Staff(
                id=uuid4(),
                restaurant_id=rest.id,
                full_name="Main Cashier",
                role=StaffRole.cashier,
                is_active=True
            )
            db.add(new_staff)
            await db.commit()
            await db.refresh(new_staff)
            staff_members = [new_staff]

    return [
        CashierOption(
            id=s.id,
            full_name=s.full_name,
            role=s.role.value if hasattr(s.role, 'value') else str(s.role),
            has_pin=bool(s.cashier_pin or s.pin_code)
        )
        for s in staff_members
    ]

@router.post("/login-pin", response_model=PinLoginResponse)
async def login_with_pin(
    request_data: PinLoginRequest,
    req: Request,
    db: AsyncSession = Depends(get_db)
):
    """Login cashier using 4-digit PIN."""
    staff = None
    if request_data.user_id:
        try:
            staff = await db.get(Staff, UUID(str(request_data.user_id)))
        except Exception:
            staff = None

    if not staff:
        # Fallback 1: find first active staff member
        stmt = select(Staff).where(Staff.is_active != False).limit(1)
        res = await db.execute(stmt)
        staff = res.scalars().first()

    if not staff:
        # Fallback 2: Auto-create default cashier staff
        stmt_r = select(Restaurant).limit(1)
        res_r = await db.execute(stmt_r)
        rest = res_r.scalars().first()
        if rest:
            staff = Staff(
                id=uuid4(),
                restaurant_id=rest.id,
                full_name="Main Cashier",
                role=StaffRole.cashier,
                is_active=True
            )
            db.add(staff)
            await db.commit()
            await db.refresh(staff)

    if not staff:
        raise HTTPException(status_code=400, detail="Invalid cashier account or staff is inactive.")

    # Check if PIN setup is required
    if not staff.cashier_pin and not staff.pin_code:
        token = create_access_token(str(staff.id))
        return PinLoginResponse(
            access_token=token,
            session_id=staff.id,
            user={
                "id": str(staff.id),
                "email": staff.email or "",
                "full_name": staff.full_name,
                "role": staff.role.value,
                "restaurant_id": str(staff.restaurant_id)
            },
            requires_pin_setup=True
        )

    try:
        verified = await pin_auth_service.verify_pin(db, request_data.user_id, request_data.pin)
        if not verified:
            raise HTTPException(status_code=400, detail="Invalid 4-digit cashier PIN code.")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    client_ip = req.client.host if req.client else None
    user_agent = req.headers.get("user-agent")

    session = await pin_auth_service.create_session(
        db,
        user_id=staff.id,
        terminal_id=request_data.terminal_id or "Terminal-1",
        ip_address=client_ip,
        user_agent=user_agent
    )

    token = create_access_token(str(staff.id))

    return PinLoginResponse(
        access_token=token,
        session_id=session.id,
        user={
            "id": str(staff.id),
            "email": staff.email or "",
            "full_name": staff.full_name,
            "role": staff.role.value,
            "restaurant_id": str(staff.restaurant_id)
        },
        requires_pin_setup=False
    )

@router.post("/setup-pin")
async def setup_pin(
    request_data: PinSetupRequest,
    db: AsyncSession = Depends(get_db)
):
    """First-time setup of cashier 4-digit PIN."""
    if request_data.pin != request_data.confirm_pin:
        raise HTTPException(status_code=400, detail="PINs do not match.")

    try:
        await pin_auth_service.setup_pin(db, request_data.user_id, request_data.pin)
        return {"status": "success", "message": "Cashier PIN setup successfully."}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/change-pin")
async def change_pin(
    request_data: PinChangeRequest,
    current_user: Staff = Depends(require_permission("process_payments")),
    db: AsyncSession = Depends(get_db)
):
    """Change cashier 4-digit PIN."""
    if request_data.new_pin != request_data.confirm_pin:
        raise HTTPException(status_code=400, detail="New PINs do not match.")

    try:
        await pin_auth_service.change_pin(db, current_user.id, request_data.current_pin, request_data.new_pin)
        return {"status": "success", "message": "Cashier PIN updated successfully."}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/reset-pin")
async def reset_pin(
    request_data: PinResetRequest,
    current_user: Staff = Depends(require_permission("manage_staff")),
    db: AsyncSession = Depends(get_db)
):
    """Manager reset cashier PIN for locked out account."""
    try:
        await pin_auth_service.reset_pin(db, request_data.user_id, request_data.new_pin, current_user.id)
        return {"status": "success", "message": "Cashier PIN reset successfully."}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/verify-pin")
async def verify_pin(
    request_data: PinVerifyRequest,
    current_user: Staff = Depends(require_permission("process_payments")),
    db: AsyncSession = Depends(get_db)
):
    """Verify PIN for sensitive terminal actions (voids, refunds, discounts)."""
    try:
        verified = await pin_auth_service.verify_pin(db, request_data.user_id, request_data.pin)
        if not verified:
            raise HTTPException(status_code=400, detail="Invalid cashier PIN code.")
        return {"status": "success", "verified": True}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/logout")
async def logout(
    request_data: LogoutRequest,
    current_user: Staff = Depends(require_permission("process_payments")),
    db: AsyncSession = Depends(get_db)
):
    """End active cashier POS session."""
    try:
        await pin_auth_service.end_session(db, request_data.session_id)
        return {"status": "success", "message": "Logged out of cashier terminal."}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/session", response_model=SessionResponse)
async def get_session(
    current_user: Staff = Depends(require_permission("process_payments")),
    db: AsyncSession = Depends(get_db)
):
    """Get active cashier session."""
    session = await pin_auth_service.get_active_session(db, current_user.id)
    if not session:
        raise HTTPException(status_code=404, detail="No active cashier session found.")
    return SessionResponse(
        id=session.id,
        user_id=session.user_id,
        terminal_id=session.terminal_id,
        logged_in_at=session.logged_in_at,
        last_activity_at=session.last_activity_at,
        logged_out_at=session.logged_out_at,
        status=session.status,
        is_active=session.status == "active"
    )

@router.post("/extend-session")
async def extend_session(
    request_data: ExtendSessionRequest,
    current_user: Staff = Depends(require_permission("process_payments")),
    db: AsyncSession = Depends(get_db)
):
    """Extend activity timestamp for current cashier session."""
    try:
        session = await pin_auth_service.extend_session(db, request_data.session_id)
        return {"status": "success", "last_activity_at": session.last_activity_at}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/lock-session")
async def lock_session(
    request_data: LockSessionRequest,
    current_user: Staff = Depends(require_permission("process_payments")),
    db: AsyncSession = Depends(get_db)
):
    """Lock cashier terminal session."""
    try:
        session = await pin_auth_service.lock_session(db, request_data.session_id)
        return {"status": "success", "status_text": session.status}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/unlock-session")
async def unlock_session(
    request_data: UnlockSessionRequest,
    current_user: Staff = Depends(require_permission("process_payments")),
    db: AsyncSession = Depends(get_db)
):
    """Unlock cashier terminal session with 4-digit PIN."""
    try:
        session = await pin_auth_service.unlock_session(db, request_data.session_id, request_data.pin)
        return {"status": "success", "status_text": session.status}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

cashier_auth_router = router
