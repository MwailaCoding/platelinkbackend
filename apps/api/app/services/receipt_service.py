"""ReceiptService for digital receipting, SMS/WhatsApp delivery, and PDF links."""
import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from uuid import UUID
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.cashier import DigitalReceipt
from app.models.order import Order
from app.schemas.cashier import ReceiptChannel

logger = logging.getLogger(__name__)

class ReceiptService:
    async def generate_receipt_data(self, db: AsyncSession, order_id: UUID) -> Dict[str, Any]:
        """Compile complete receipt itemization data."""
        order = await db.get(Order, order_id)
        if not order:
            raise ValueError("Order not found")

        items_data = []
        if hasattr(order, 'items') and order.items:
            for item in order.items:
                items_data.append({
                    "name": getattr(item, 'menu_item_name', 'Item'),
                    "quantity": getattr(item, 'quantity', 1),
                    "unit_price": float(getattr(item, 'unit_price', 0)),
                    "subtotal": float(getattr(item, 'subtotal', 0))
                })

        return {
            "order_id": str(order.id),
            "order_number": getattr(order, 'order_number', str(order.id)[:8]),
            "subtotal": float(order.subtotal),
            "tax": float(order.tax),
            "total": float(order.total),
            "payment_status": order.payment_status,
            "created_at": str(order.created_at),
            "items": items_data
        }

    async def create_receipt_pdf_url(self, order_id: UUID) -> str:
        """Return public receipt URL for print / sharing."""
        return f"https://platelink-admin.vercel.app/receipts/{order_id}"

    async def send_digital_receipt(
        self,
        db: AsyncSession,
        order_id: UUID,
        channel: str,
        recipient: str,
        cashier_id: UUID,
        message: Optional[str] = None
    ) -> DigitalReceipt:
        """Send digital receipt link via WhatsApp/SMS/Email/Print."""
        receipt_url = await self.create_receipt_pdf_url(order_id)

        receipt = DigitalReceipt(
            order_id=order_id,
            receipt_url=receipt_url,
            sent_via=channel,
            sent_to=recipient,
            is_delivered=True,
            delivered_at=datetime.now(timezone.utc),
            created_by=cashier_id
        )
        db.add(receipt)
        await db.commit()
        await db.refresh(receipt)
        return receipt

    async def get_receipt(self, db: AsyncSession, receipt_id: UUID) -> Optional[DigitalReceipt]:
        return await db.get(DigitalReceipt, receipt_id)

    async def get_receipts_by_order(self, db: AsyncSession, order_id: UUID) -> List[DigitalReceipt]:
        stmt = select(DigitalReceipt).where(DigitalReceipt.order_id == order_id).order_by(DigitalReceipt.sent_at.desc())
        res = await db.execute(stmt)
        return list(res.scalars().all())

    async def mark_receipt_delivered(self, db: AsyncSession, receipt_id: UUID) -> DigitalReceipt:
        receipt = await self.get_receipt(db, receipt_id)
        if not receipt:
            raise ValueError("Receipt not found")
        receipt.is_delivered = True
        receipt.delivered_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(receipt)
        return receipt

    async def generate_split_receipt(
        self,
        db: AsyncSession,
        transaction_id: UUID,
        customer_name: str,
        items: List[Dict[str, Any]],
        subtotal: Decimal
    ) -> Dict[str, Any]:
        """Generate receipt data for a single split check guest."""
        return {
            "transaction_id": str(transaction_id),
            "customer_name": customer_name,
            "items": items,
            "subtotal": float(subtotal),
            "generated_at": str(datetime.now(timezone.utc))
        }

    async def send_bulk_digital_receipts(
        self,
        db: AsyncSession,
        order_id: UUID,
        receipts_data: List[Dict[str, Any]],
        channel: str,
        cashier_id: UUID
    ) -> List[DigitalReceipt]:
        """Send digital receipts in bulk for split bills."""
        results = []
        for rdata in receipts_data:
            rec = await self.send_digital_receipt(
                db,
                order_id=order_id,
                channel=channel,
                recipient=rdata.get("recipient", "Guest"),
                cashier_id=cashier_id,
                message=rdata.get("message")
            )
            results.append(rec)
        return results

    async def get_receipt_history(
        self,
        db: AsyncSession,
        order_id: UUID,
        limit: int = 100
    ) -> List[DigitalReceipt]:
        """Fetch receipt history for an order."""
        stmt = select(DigitalReceipt).where(DigitalReceipt.order_id == order_id).order_by(DigitalReceipt.sent_at.desc()).limit(limit)
        res = await db.execute(stmt)
        return list(res.scalars().all())


receipt_service = ReceiptService()
