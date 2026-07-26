"""TillService for shift management, cash reconciliation, and Z-report generation."""
import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from uuid import UUID
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.cashier import CashierShift, PaymentTransaction
from app.models.staff import Staff
from app.schemas.cashier import (
    ShiftStatus,
    ShiftSummaryResponse,
    ZReportResponse,
    PaymentMethod,
    PaymentStatus
)

logger = logging.getLogger(__name__)

class TillService:
    async def open_shift(
        self,
        db: AsyncSession,
        terminal_id: str,
        cashier_id: UUID,
        opening_float: Decimal,
        notes: Optional[str] = None
    ) -> CashierShift:
        """Open a new till shift for a specific cashier/restaurant."""
        # Check if cashier already has an active open shift
        stmt = select(CashierShift).where(
            CashierShift.cashier_id == cashier_id,
            CashierShift.status == ShiftStatus.OPEN.value
        )
        res = await db.execute(stmt)
        existing = res.scalar_one_or_none()
        if existing:
            raise ValueError(f"Cashier already has an active open shift on terminal {existing.terminal_id}.")

        shift = CashierShift(
            terminal_id=terminal_id,
            cashier_id=cashier_id,
            opening_float=opening_float,
            status=ShiftStatus.OPEN.value,
            notes=notes
        )
        db.add(shift)
        await db.commit()
        await db.refresh(shift)
        return shift

    async def get_current_shift(
        self,
        db: AsyncSession,
        terminal_id: str = "Terminal-1",
        cashier_id: Optional[UUID] = None
    ) -> Optional[CashierShift]:
        """Get active open shift for terminal and cashier."""
        stmt = select(CashierShift).where(
            CashierShift.status == ShiftStatus.OPEN.value
        )
        if cashier_id:
            stmt = stmt.where(CashierShift.cashier_id == cashier_id)
        else:
            stmt = stmt.where(CashierShift.terminal_id == terminal_id)

        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_shift(self, db: AsyncSession, shift_id: UUID) -> Optional[CashierShift]:
        return await db.get(CashierShift, shift_id)

    async def close_shift(
        self,
        db: AsyncSession,
        shift_id: UUID,
        actual_cash: Decimal,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Close shift and calculate variance."""
        shift = await self.get_shift(db, shift_id)
        if not shift:
            raise ValueError("Shift not found")
        if shift.status == ShiftStatus.CLOSED.value:
            raise ValueError("Shift is already closed")

        # Sum completed cash sales for shift
        stmt = select(func.coalesce(func.sum(PaymentTransaction.amount), 0)).where(
            PaymentTransaction.shift_id == shift_id,
            PaymentTransaction.method == PaymentMethod.CASH.value,
            PaymentTransaction.status == PaymentStatus.COMPLETED.value
        )
        res = await db.execute(stmt)
        cash_sales = Decimal(str(res.scalar() or 0))

        # Sum M-Pesa
        stmt_mpesa = select(func.coalesce(func.sum(PaymentTransaction.amount), 0)).where(
            PaymentTransaction.shift_id == shift_id,
            PaymentTransaction.method == PaymentMethod.MPESA.value,
            PaymentTransaction.status == PaymentStatus.COMPLETED.value
        )
        res_mpesa = await db.execute(stmt_mpesa)
        mpesa_sales = Decimal(str(res_mpesa.scalar() or 0))

        # Sum Card
        stmt_card = select(func.coalesce(func.sum(PaymentTransaction.amount), 0)).where(
            PaymentTransaction.shift_id == shift_id,
            PaymentTransaction.method == PaymentMethod.CARD.value,
            PaymentTransaction.status == PaymentStatus.COMPLETED.value
        )
        res_card = await db.execute(stmt_card)
        card_sales = Decimal(str(res_card.scalar() or 0))

        expected_cash = shift.opening_float + cash_sales
        variance = actual_cash - expected_cash

        shift.closing_float = actual_cash
        shift.expected_cash = expected_cash
        shift.actual_cash = actual_cash
        shift.variance = variance
        shift.closed_at = datetime.now(timezone.utc)
        shift.status = ShiftStatus.CLOSED.value
        if notes:
            shift.notes = (shift.notes or "") + f" | Closing Notes: {notes}"

        await db.commit()
        await db.refresh(shift)

        total_sales = cash_sales + mpesa_sales + card_sales

        return {
            "id": shift.id,
            "terminal_id": shift.terminal_id,
            "expected_cash": expected_cash,
            "actual_cash": actual_cash,
            "variance": variance,
            "closed_at": shift.closed_at,
            "cash_sales": cash_sales,
            "mpesa_sales": mpesa_sales,
            "card_sales": card_sales,
            "total_sales": total_sales
        }

    async def get_shift_summary(self, db: AsyncSession, shift_id: UUID) -> ShiftSummaryResponse:
        """Compile detailed metrics summary for a shift."""
        shift = await self.get_shift(db, shift_id)
        if not shift:
            raise ValueError("Shift not found")

        cashier = await db.get(Staff, shift.cashier_id)
        cashier_name = cashier.full_name if cashier else "Cashier"

        # Calculate sales by method
        stmt = select(
            PaymentTransaction.method,
            func.coalesce(func.sum(PaymentTransaction.amount), 0),
            func.count(PaymentTransaction.id)
        ).where(
            PaymentTransaction.shift_id == shift_id,
            PaymentTransaction.status == PaymentStatus.COMPLETED.value
        ).group_by(PaymentTransaction.method)

        res = await db.execute(stmt)
        rows = res.all()

        cash_sales = Decimal("0.00")
        mpesa_sales = Decimal("0.00")
        card_sales = Decimal("0.00")
        tx_count = 0

        for row in rows:
            m, amt, cnt = row[0], Decimal(str(row[1])), row[2]
            tx_count += cnt
            if m == PaymentMethod.CASH.value:
                cash_sales += amt
            elif m == PaymentMethod.MPESA.value:
                mpesa_sales += amt
            elif m == PaymentMethod.CARD.value:
                card_sales += amt

        expected_cash = shift.opening_float + cash_sales
        total_sales = cash_sales + mpesa_sales + card_sales

        return ShiftSummaryResponse(
            shift_id=shift.id,
            cashier_name=cashier_name,
            terminal_id=shift.terminal_id,
            opened_at=shift.opened_at,
            closed_at=shift.closed_at,
            opening_float=shift.opening_float,
            expected_cash=expected_cash,
            actual_cash=shift.actual_cash,
            variance=shift.variance,
            cash_sales=cash_sales,
            mpesa_sales=mpesa_sales,
            card_sales=card_sales,
            total_sales=total_sales,
            transaction_count=tx_count
        )

    async def generate_z_report(self, db: AsyncSession, shift_id: UUID) -> ZReportResponse:
        """Generate Z-Report for end-of-shift reconciliation."""
        summary = await self.get_shift_summary(db, shift_id)

        # Get hourly breakdown
        stmt = select(
            func.to_char(PaymentTransaction.processed_at, 'HH24:00').label('hour'),
            func.coalesce(func.sum(PaymentTransaction.amount), 0).label('amount'),
            func.count(PaymentTransaction.id).label('count')
        ).where(
            PaymentTransaction.shift_id == shift_id,
            PaymentTransaction.status == PaymentStatus.COMPLETED.value
        ).group_by('hour').order_by('hour')

        res = await db.execute(stmt)
        hourly = [{"hour": row[0], "amount": float(row[1]), "count": row[2]} for row in res.all()]

        return ZReportResponse(
            shift_id=shift_id,
            generated_at=datetime.now(timezone.utc),
            summary=summary,
            transaction_breakdown={"total_completed": summary.transaction_count},
            payment_method_breakdown={
                "cash": summary.cash_sales,
                "mpesa": summary.mpesa_sales,
                "card": summary.card_sales
            },
            hourly_breakdown=hourly,
            status=summary.closed_at and "CLOSED" or "ACTIVE"
        )

till_service = TillService()
