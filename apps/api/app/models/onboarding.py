"""OnboardingStatus model for tracking restaurant onboarding steps."""
from datetime import datetime
from typing import Optional, List
from uuid import UUID
from sqlalchemy import text, Boolean, DateTime, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, ARRAY, VARCHAR
from app.models.base import Base

class OnboardingStatus(Base):
    __tablename__ = "onboarding_status"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    restaurant_id: Mapped[UUID] = mapped_column(ForeignKey("restaurants.id", ondelete="CASCADE"), unique=True, nullable=False)
    step_completed: Mapped[List[str]] = mapped_column(ARRAY(VARCHAR(100)), default=list, server_default="{}")
    is_complete: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationship
    restaurant: Mapped["Restaurant"] = relationship("Restaurant", back_populates="onboarding_status")
