"""PaymentService for handling M-Pesa STK Push, Cash, Card, and transactions."""
import logging
from datetime import datetime, date, timezone
from typing import List, Optional, Dict, Any
from uuid import UUID
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.cashier import PaymentTransaction, CashierShift
from app.models.order import Order
from app.models.staff import Staff
from app.schemas.cashier import PaymentStatus, PaymentMethod

logger = logging.getLogger(__name__)

class PaymentService:
    async def process_mpesa_payment(
        self,
        db: AsyncSession,
        order_id: UUID,
        phone: str,
        amount: Optional[Decimal],
        cashier_id: UUID,
        shift_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Initiate M-Pesa STK Push payment and record pending transaction."""
        order = await db.get(Order, order_id)
        if not order:
            raise ValueError("Order not found")

        pay_amount = amount or Decimal(str(order.total))

        # Create pending transaction
        tx = PaymentTransaction(
            order_id=order_id,
            restaurant_id=order.restaurant_id,
            branch_id=order.branch_id,
            amount=pay_amount,
            method=PaymentMethod.MPESA.value,
            status=PaymentStatus.PENDING.value,
            mpesa_phone=phone,
            processed_by=cashier_id,
            shift_id=shift_id
        )
        db.add(tx)
        await db.commit()
        await db.refresh(tx)

        # Mock / Real STK Push IDs
        merchant_req_id = f"MR_{tx.id.hex[:12]}"
        checkout_req_id = f"WS_{tx.id.hex[:16]}"
        tx.reference = merchant_req_id
        await db.commit()

        return {
            "transaction_id": tx.id,
            "order_id": order_id,
            "amount": pay_amount,
            "status": PaymentStatus.PENDING.value,
            "mpesa_receipt": None,
            "phone_number": phone,
            "merchant_request_id": merchant_req_id,
            "checkout_request_id": checkout_req_id
        }

    async def process_cash_payment(
        self,
        db: AsyncSession,
        order_id: UUID,
        amount_received: Decimal,
        cashier_id: UUID,
        shift_id: Optional[UUID] = None,
        notes: Optional[str] = None
    ) -> PaymentTransaction:
        """Process cash payment, calculate change, mark order paid."""
        order = await db.get(Order, order_id)
        if not order:
            raise ValueError("Order not found")

        pay_amount = Decimal(str(order.total))
        if amount_received < pay_amount:
            raise ValueError("Amount received is less than total due")

        change = amount_received - pay_amount

        tx = PaymentTransaction(
            order_id=order_id,
            restaurant_id=order.restaurant_id,
            branch_id=order.branch_id,
            amount=pay_amount,
            method=PaymentMethod.CASH.value,
            status=PaymentStatus.COMPLETED.value,
            cash_received=amount_received,
            cash_change=change,
            processed_by=cashier_id,
            shift_id=shift_id,
            settled_at=datetime.now(timezone.utc),
            notes=notes
        )
        db.add(tx)

        # Mark order paid
        order.payment_status = "paid"
        order.status = "completed"

        await db.commit()
        await db.refresh(tx)
        return tx

    async def process_card_payment(
        self,
        db: AsyncSession,
        order_id: UUID,
        card_reference: str,
        amount: Optional[Decimal],
        cashier_id: UUID,
        shift_id: Optional[UUID] = None,
        notes: Optional[str] = None
    ) -> PaymentTransaction:
        """Process PDQ Card payment."""
        order = await db.get(Order, order_id)
        if not order:
            raise ValueError("Order not found")

        pay_amount = amount or Decimal(str(order.total))

        tx = PaymentTransaction(
            order_id=order_id,
            restaurant_id=order.restaurant_id,
            branch_id=order.branch_id,
            amount=pay_amount,
            method=PaymentMethod.CARD.value,
            status=PaymentStatus.COMPLETED.value,
            card_reference=card_reference,
            processed_by=cashier_id,
            shift_id=shift_id,
            settled_at=datetime.now(timezone.utc),
            notes=notes
        )
        db.add(tx)

        order.payment_status = "paid"
        order.status = "completed"

        await db.commit()
        await db.refresh(tx)
        return tx

    async def confirm_mpesa_payment(
        self,
        db: AsyncSession,
        merchant_request_id: str,
        mpesa_receipt: str
    ) -> PaymentTransaction:
        """Confirm M-Pesa transaction by merchant_request_id."""
        stmt = select(PaymentTransaction).where(PaymentTransaction.reference == merchant_request_id)
        res = await db.execute(stmt)
        tx = res.scalar_one_or_none()

        if not tx:
            raise ValueError("Transaction not found for merchant_request_id")

        tx.status = PaymentStatus.COMPLETED.value
        tx.mpesa_receipt = mpesa_receipt
        tx.settled_at = datetime.now(timezone.utc)

        order = await db.get(Order, tx.order_id)
        if order:
            order.payment_status = "paid"
            order.status = "completed"

        await db.commit()
        await db.refresh(tx)
        return tx

    async def get_transaction(self, db: AsyncSession, transaction_id: UUID) -> Optional[PaymentTransaction]:
        return await db.get(PaymentTransaction, transaction_id)

    async def get_transactions_by_order(self, db: AsyncSession, order_id: UUID) -> List[PaymentTransaction]:
        stmt = select(PaymentTransaction).where(PaymentTransaction.order_id == order_id).order_by(PaymentTransaction.processed_at.desc())
        res = await db.execute(stmt)
        return list(res.scalars().all())

    async def get_transactions_by_shift(self, db: AsyncSession, shift_id: UUID) -> List[PaymentTransaction]:
        stmt = select(PaymentTransaction).where(PaymentTransaction.shift_id == shift_id).order_by(PaymentTransaction.processed_at.desc())
        res = await db.execute(stmt)
        return list(res.scalars().all())

    async def get_transactions_by_cashier(
        self,
        db: AsyncSession,
        cashier_id: UUID,
        start_date: date,
        end_date: date
    ) -> List[PaymentTransaction]:
        stmt = select(PaymentTransaction).where(
            PaymentTransaction.processed_by == cashier_id,
            func.date(PaymentTransaction.processed_at) >= start_date,
            func.date(PaymentTransaction.processed_at) <= end_date
        ).order_by(PaymentTransaction.processed_at.desc())
        res = await db.execute(stmt)
        return list(res.scalars().all())

    async def void_transaction(
        self,
        db: AsyncSession,
        transaction_id: UUID,
        cashier_id: UUID,
        reason: str
    ) -> PaymentTransaction:
        tx = await self.get_transaction(db, transaction_id)
        if not tx:
            raise ValueError("Transaction not found")

        tx.status = PaymentStatus.VOIDED.value
        tx.notes = f"Voided by {cashier_id}: {reason}"
        await db.commit()
        await db.refresh(tx)
        return tx

    async def split_bill_equal(
        self,
        db: AsyncSession,
        order_id: UUID,
        num_people: int,
        cashier_id: UUID,
        shift_id: Optional[UUID] = None
    ) -> List[PaymentTransaction]:
        """Split order bill equally among N people."""
        order = await db.get(Order, order_id)
        if not order:
            raise ValueError("Order not found")
        if num_people < 2:
            raise ValueError("Must split among at least 2 people")

        per_person = round(Decimal(str(order.total)) / Decimal(num_people), 2)
        transactions = []

        for i in range(num_people):
            tx = PaymentTransaction(
                order_id=order_id,
                restaurant_id=order.restaurant_id,
                branch_id=order.branch_id,
                amount=per_person,
                method=PaymentMethod.SPLIT.value,
                status=PaymentStatus.PENDING.value,
                reference=f"SPLIT-{order_id.hex[:6]}-{i+1}",
                processed_by=cashier_id,
                shift_id=shift_id,
                notes=f"Equal split {i+1} of {num_people}"
            )
            db.add(tx)
            transactions.append(tx)

        order.payment_status = "partially_paid"
        await db.commit()
        for t in transactions:
            await db.refresh(t)
        return transactions

    async def split_bill_by_items(
        self,
        db: AsyncSession,
        order_id: UUID,
        assignments: List[Dict[str, Any]],
        cashier_id: UUID,
        shift_id: Optional[UUID] = None
    ) -> List[PaymentTransaction]:
        """Split order bill by itemized assignments per customer."""
        order = await db.get(Order, order_id)
        if not order:
            raise ValueError("Order not found")

        # Group amounts by customer_id
        customer_totals: Dict[str, Decimal] = {}
        for item in assignments:
            cid = item.get("customer_id", "Customer")
            price = Decimal(str(item.get("price", 0)))
            qty = Decimal(str(item.get("quantity", 1)))
            customer_totals[cid] = customer_totals.get(cid, Decimal("0.00")) + (price * qty)

        transactions = []
        for cid, total in customer_totals.items():
            tx = PaymentTransaction(
                order_id=order_id,
                restaurant_id=order.restaurant_id,
                branch_id=order.branch_id,
                amount=total,
                method=PaymentMethod.SPLIT.value,
                status=PaymentStatus.PENDING.value,
                reference=f"ITEMSPLIT-{cid[:8]}",
                processed_by=cashier_id,
                shift_id=shift_id,
                notes=f"Itemized split for {cid}"
            )
            db.add(tx)
            transactions.append(tx)

        order.payment_status = "partially_paid"
        await db.commit()
        for t in transactions:
            await db.refresh(t)
        return transactions

    async def get_split_status(self, db: AsyncSession, order_id: UUID) -> Dict[str, Any]:
        """Get current split bill status for an order."""
        txs = await self.get_transactions_by_order(db, order_id)
        order = await db.get(Order, order_id)
        if not order:
            raise ValueError("Order not found")

        total_settled = sum(t.amount for t in txs if t.status == PaymentStatus.COMPLETED.value)
        total_due = Decimal(str(order.total))

        return {
            "order_id": str(order_id),
            "total": float(total_due),
            "total_settled": float(total_settled),
            "remaining": float(total_due - total_settled),
            "transactions_count": len(txs),
            "status": "complete" if total_settled >= total_due else "partial" if total_settled > 0 else "pending"
        }


payment_service = PaymentService()
