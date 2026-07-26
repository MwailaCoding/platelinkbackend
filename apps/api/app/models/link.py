"""Link model for managing restaurant access links and custom domains."""
from datetime import datetime, timezone
from typing import Optional, List
from uuid import UUID
from sqlalchemy import text, Text, Boolean, DateTime, func, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from app.models.base import Base

class Link(Base):
    __tablename__ = "links"

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
    type: Mapped[str] = mapped_column(Text, nullable=False, default="primary")
    slug: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    custom_domain: Mapped[Optional[str]] = mapped_column(Text, unique=True, nullable=True)
    domain_verified: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
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
    restaurant: Mapped["Restaurant"] = relationship("Restaurant", overlaps="links")
    branch: Mapped[Optional["Branches"]] = relationship("Branches", overlaps="links")
    analytics: Mapped[List["LinkAnalytics"]] = relationship("LinkAnalytics", back_populates="link", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_links_restaurant_id", "restaurant_id"),
        Index("ix_links_type", "type"),
        Index("ix_links_slug", "slug"),
        Index("ix_links_custom_domain", "custom_domain"),
    )
