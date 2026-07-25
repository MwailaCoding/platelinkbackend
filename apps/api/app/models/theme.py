"""Theme model for brand theme presets."""
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID
from sqlalchemy import text, Text, Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB, VARCHAR
from app.models.base import Base

class Theme(Base):
    __tablename__ = "themes"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    name: Mapped[str] = mapped_column(VARCHAR(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    preview_image: Mapped[Optional[str]] = mapped_column(VARCHAR(255), nullable=True)
    template_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
