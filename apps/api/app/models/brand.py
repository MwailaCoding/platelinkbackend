"""BrandSettings and Theme models for restaurant visual customization."""
from datetime import datetime
from typing import Optional, Dict, Any, TYPE_CHECKING
from uuid import UUID
from sqlalchemy import text, Text, Boolean, DateTime, func, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB, VARCHAR
from app.models.base import Base

if TYPE_CHECKING:
    from app.models.restaurant import Restaurant


class BrandSettings(Base):
    __tablename__ = "brand_settings"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    restaurant_id: Mapped[UUID] = mapped_column(ForeignKey("restaurants.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    # Color scheme
    primary_color: Mapped[str] = mapped_column(VARCHAR(7), default="#F97316", server_default="'#F97316'")
    secondary_color: Mapped[str] = mapped_column(VARCHAR(7), default="#0A1628", server_default="'#0A1628'")
    background_color: Mapped[str] = mapped_column(VARCHAR(7), default="#F8FAFC", server_default="'#F8FAFC'")
    text_color: Mapped[str] = mapped_column(VARCHAR(7), default="#0A1628", server_default="'#0A1628'")
    accent_color: Mapped[str] = mapped_column(VARCHAR(7), default="#10B981", server_default="'#10B981'")
    
    # Asset URLs
    logo_url: Mapped[Optional[str]] = mapped_column(VARCHAR(255), nullable=True)
    hero_image_url: Mapped[Optional[str]] = mapped_column(VARCHAR(255), nullable=True)
    favicon_url: Mapped[Optional[str]] = mapped_column(VARCHAR(255), nullable=True)
    
    # Typography
    heading_font: Mapped[str] = mapped_column(VARCHAR(100), default="Inter", server_default="'Inter'")
    body_font: Mapped[str] = mapped_column(VARCHAR(100), default="Inter", server_default="'Inter'")
    
    # Branding Text & Messages
    welcome_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tagline: Mapped[Optional[str]] = mapped_column(VARCHAR(255), nullable=True)
    footer_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Social Links
    instagram_url: Mapped[Optional[str]] = mapped_column(VARCHAR(255), nullable=True)
    facebook_url: Mapped[Optional[str]] = mapped_column(VARCHAR(255), nullable=True)
    twitter_url: Mapped[Optional[str]] = mapped_column(VARCHAR(255), nullable=True)
    youtube_url: Mapped[Optional[str]] = mapped_column(VARCHAR(255), nullable=True)
    
    # Layout & Component Styles
    card_style: Mapped[str] = mapped_column(VARCHAR(20), default="rounded", server_default="'rounded'")
    button_style: Mapped[str] = mapped_column(VARCHAR(20), default="filled", server_default="'filled'")
    category_display: Mapped[str] = mapped_column(VARCHAR(20), default="tabs", server_default="'tabs'")
    cart_behavior: Mapped[str] = mapped_column(VARCHAR(20), default="bottom_bar", server_default="'bottom_bar'")
    
    # Code Customizations
    custom_css: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    custom_js: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    restaurant: Mapped["Restaurant"] = relationship("Restaurant", back_populates="brand_settings", foreign_keys=[restaurant_id])


class Theme(Base):
    __tablename__ = "themes"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    name: Mapped[str] = mapped_column(VARCHAR(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    preview_image: Mapped[Optional[str]] = mapped_column(VARCHAR(255), nullable=True)
    template_data: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    price: Mapped[float] = mapped_column(Numeric(10, 2), default=0, server_default="0.00")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
