"""Till and Shift endpoints for Cashier POS Terminal Turbo."""
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.core.dependencies import require_permission
from app.models.staff import Staff
from app.schemas.cashier import (
    ShiftOpenRequest, ShiftOpenResponse,
    ShiftCloseRequest, ShiftCloseResponse,
    ShiftSummaryResponse, ZReportResponse
)
from app.services.till_service import till_service

from pydantic import BaseModel
from typing import List
from sqlalchemy import select
from app.models.branch import Branch

class TerminalOption(BaseModel):
    id: str
    name: str

router = APIRouter(prefix="/till", tags=["till"])

@router.get("/terminals", response_model=List[TerminalOption])
async def list_terminals(
    db: AsyncSession = Depends(get_db)
):
    """List dynamic till terminals for restaurant."""
    stmt = select(Branch).where(Branch.is_active == True)
    res = await db.execute(stmt)
    branches = res.scalars().all()
    if branches:
        return [
            TerminalOption(id=f"POS-{b.id.hex[:6]}", name=f"{b.name} POS Counter")
            for b in branches
        ]
    return [
        TerminalOption(id="Terminal-Main", name="Main Till Counter"),
        TerminalOption(id="Terminal-Bar", name="Bar & Drinks Counter"),
        TerminalOption(id="Terminal-Terrace", name="Terrace / Outdoor POS"),
    ]

@router.post("/shift/open", response_model=ShiftOpenResponse)
async def open_shift(
    request: ShiftOpenRequest,
    current_user: Staff = Depends(require_permission("manage_till")),
    db: AsyncSession = Depends(get_db)
):
    """Open a new till shift."""
    if request.pin_code and current_user.pin_code and current_user.pin_code != request.pin_code:
        raise HTTPException(status_code=400, detail="Invalid cashier 4-digit PIN code.")
    try:
        shift = await till_service.open_shift(
            db,
            terminal_id=request.terminal_id,
            cashier_id=current_user.id,
            opening_float=request.opening_float,
            notes=request.notes
        )
        return shift
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/shift/close", response_model=ShiftCloseResponse)
async def close_shift(
    shift_id: UUID,
    request: ShiftCloseRequest,
    current_user: Staff = Depends(require_permission("manage_till")),
    db: AsyncSession = Depends(get_db)
):
    """Close current active till shift."""
    try:
        closed_data = await till_service.close_shift(
            db,
            shift_id=shift_id,
            actual_cash=request.actual_cash,
            notes=request.notes
        )
        return closed_data
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/shift/current", response_model=Optional[ShiftOpenResponse])
async def get_current_shift(
    terminal_id: str = "Terminal-1",
    current_user: Staff = Depends(require_permission("manage_till")),
    db: AsyncSession = Depends(get_db)
):
    """Get current active open shift for terminal and cashier."""
    shift = await till_service.get_current_shift(db, terminal_id=terminal_id, cashier_id=current_user.id)
    return shift

@router.get("/shift/{shift_id}", response_model=ShiftSummaryResponse)
async def get_shift_summary(
    shift_id: UUID,
    current_user: Staff = Depends(require_permission("manage_till")),
    db: AsyncSession = Depends(get_db)
):
    """Get shift summary details."""
    try:
        return await till_service.get_shift_summary(db, shift_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/shift/{shift_id}/z-report", response_model=ZReportResponse)
async def generate_z_report(
    shift_id: UUID,
    current_user: Staff = Depends(require_permission("manage_till")),
    db: AsyncSession = Depends(get_db)
):
    """Generate Z-Report for end-of-shift reconciliation."""
    try:
        return await till_service.generate_z_report(db, shift_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
