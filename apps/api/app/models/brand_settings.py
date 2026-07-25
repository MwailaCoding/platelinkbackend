"""BrandSettings model for restaurant visual customization."""
from datetime import datetime
from typing import Optional
from uuid import UUID
from sqlalchemy import text, Text, DateTime, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, VARCHAR
from app.models.base import Base

class BrandSettings(Base):
    __tablename__ = "brand_settings"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    restaurant_id: Mapped[UUID] = mapped_column(ForeignKey("restaurants.id", ondelete="CASCADE"), unique=True, nullable=False)
    logo_url: Mapped[Optional[str]] = mapped_column(VARCHAR(255), nullable=True)
    hero_image_url: Mapped[Optional[str]] = mapped_column(VARCHAR(255), nullable=True)
    primary_color: Mapped[str] = mapped_column(VARCHAR(7), default="#F97316", server_default="'#F97316'")
    secondary_color: Mapped[str] = mapped_column(VARCHAR(7), default="#0A1628", server_default="'#0A1628'")
    theme_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("themes.id", ondelete="SET NULL"), nullable=True)
    custom_css: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    restaurant: Mapped["Restaurant"] = relationship("Restaurant", back_populates="brand_settings")
    theme: Mapped[Optional["Theme"]] = relationship("Theme")
