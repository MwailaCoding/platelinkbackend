"""QRCode model for managing table QR codes and design metadata."""
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from uuid import UUID
from sqlalchemy import text, Text, Boolean, DateTime, Integer, func, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from app.models.base import Base

class QRCode(Base):
    __tablename__ = "qr_codes"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )
    restaurant_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("restaurants.id", ondelete="CASCADE"),
        nullable=False
    )
    branch_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("branches.id", ondelete="SET NULL"),
        nullable=True
    )
    table_number: Mapped[str] = mapped_column(Text, nullable=False)
    qr_data: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    qr_image_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    scan_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    order_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    last_scanned: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        onupdate=func.now()
    )

    # Relationships
    restaurant: Mapped["Restaurant"] = relationship("Restaurant", overlaps="qr_codes")
    branch: Mapped[Optional["Branches"]] = relationship("Branches", overlaps="qr_codes")

    __table_args__ = (
        Index("ix_qr_codes_restaurant_id", "restaurant_id"),
        Index("ix_qr_codes_branch_id", "branch_id"),
        Index("ix_qr_codes_table_number", "table_number"),
    )
