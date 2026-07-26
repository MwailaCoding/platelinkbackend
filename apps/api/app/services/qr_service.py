"""QRService for generating, styling, tracking, and bundling table QR codes into ZIP archives."""
import io
import zipfile
import logging
from datetime import date, datetime, timezone
from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import qrcode
from qrcode.image.pil import PilImage

from app.models.qr import QRCode
from app.models.restaurant import Restaurant
from app.schemas.qr import QRDesignData

logger = logging.getLogger(__name__)

class QRService:
    @staticmethod
    def generate_qr_png_bytes(target_url: str, primary_color: str = "#F97316") -> bytes:
        """Generate high-res PNG bytes for a given QR target URL."""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=2,
        )
        qr.add_data(target_url)
        qr.make(fit=True)

        img = qr.make_image(fill_color=primary_color, back_color="white")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    async def generate_table_qr(
        self,
        db: AsyncSession,
        table_number: str,
        restaurant_id: UUID,
        branch_id: Optional[UUID] = None,
        design: Optional[QRDesignData] = None
    ) -> QRCode:
        """Generate or update table QR record."""
        design_dict = design.model_dump() if design else {
            "primary_color": "#F97316",
            "secondary_color": "#0A1628",
            "frame_text": "Scan to Order",
            "border_style": "rounded"
        }

        # Check existing
        stmt = select(QRCode).where(
            QRCode.restaurant_id == restaurant_id,
            QRCode.table_number == table_number,
            QRCode.branch_id == branch_id
        )
        result = await db.execute(stmt)
        qr_obj = result.scalar_one_or_none()

        target_url = f"https://platelink.africa/t/{restaurant_id}/table/{table_number}"
        cdn_url = f"https://cdn.platelink.africa/qr/{restaurant_id}/{table_number}.png"

        if qr_obj:
            qr_obj.qr_data = design_dict
            qr_obj.qr_image_url = cdn_url
            qr_obj.updated_at = datetime.now(timezone.utc)
        else:
            qr_obj = QRCode(
                restaurant_id=restaurant_id,
                branch_id=branch_id,
                table_number=table_number,
                qr_data=design_dict,
                qr_image_url=cdn_url
            )
            db.add(qr_obj)

        await db.commit()
        await db.refresh(qr_obj)
        return qr_obj

    async def bulk_generate_qr(
        self,
        db: AsyncSession,
        table_numbers: List[str],
        restaurant_id: UUID,
        branch_id: Optional[UUID] = None,
        design: Optional[QRDesignData] = None
    ) -> List[QRCode]:
        """Bulk generate table QR codes."""
        created_list = []
        for t_num in table_numbers:
            qr_item = await self.generate_table_qr(
                db=db,
                table_number=t_num,
                restaurant_id=restaurant_id,
                branch_id=branch_id,
                design=design
            )
            created_list.append(qr_item)
        return created_list

    async def get_table_qr(self, db: AsyncSession, table_number: str, restaurant_id: UUID) -> Optional[QRCode]:
        """Retrieve table QR by table number."""
        stmt = select(QRCode).where(
            QRCode.restaurant_id == restaurant_id,
            QRCode.table_number == table_number
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def increment_scan_count(self, db: AsyncSession, qr_id: UUID) -> None:
        """Increment scan count for a QR code."""
        qr_obj = await db.get(QRCode, qr_id)
        if qr_obj:
            qr_obj.scan_count += 1
            qr_obj.last_scanned = datetime.now(timezone.utc)
            await db.commit()

    async def increment_order_count(self, db: AsyncSession, qr_id: UUID) -> None:
        """Increment order count for a QR code."""
        qr_obj = await db.get(QRCode, qr_id)
        if qr_obj:
            qr_obj.order_count += 1
            await db.commit()

    def design_qr_with_branding(self, qr_code_obj: QRCode, brand_settings: Dict[str, Any]) -> bytes:
        """Return styled PNG bytes for print/download."""
        primary_color = brand_settings.get("primary_color", "#F97316")
        url = f"https://platelink.africa/t/{qr_code_obj.restaurant_id}/table/{qr_code_obj.table_number}"
        return self.generate_qr_png_bytes(url, primary_color=primary_color)

    async def download_all_qr_codes(self, db: AsyncSession, restaurant_id: UUID) -> bytes:
        """Generate ZIP file containing high-res PNG images of all table QR codes for a restaurant."""
        stmt = select(QRCode).where(QRCode.restaurant_id == restaurant_id, QRCode.is_active == True)
        result = await db.execute(stmt)
        qr_items = result.scalars().all()

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for qr in qr_items:
                target_url = f"https://platelink.africa/t/{restaurant_id}/table/{qr.table_number}"
                png_bytes = self.generate_qr_png_bytes(target_url, primary_color=qr.qr_data.get("primary_color", "#F97316"))
                filename = f"Table_{qr.table_number}_QR.png"
                zf.writestr(filename, png_bytes)

        return zip_buffer.getvalue()

    async def get_qr_analytics(self, db: AsyncSession, qr_id: UUID, start_date: date, end_date: date) -> Dict[str, Any]:
        """Fetch QR analytics stats."""
        qr_obj = await db.get(QRCode, qr_id)
        if not qr_obj:
            return {}
        return {
            "qr_id": str(qr_obj.id),
            "table_number": qr_obj.table_number,
            "scan_count": qr_obj.scan_count,
            "order_count": qr_obj.order_count,
            "last_scanned": qr_obj.last_scanned,
            "conversion_rate": round((qr_obj.order_count / qr_obj.scan_count * 100) if qr_obj.scan_count > 0 else 0, 2)
        }

qr_service = QRService()
