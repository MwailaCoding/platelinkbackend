"""LinkAnalytics model for tracking link performance and traffic analytics."""
from datetime import datetime, date, timezone
from uuid import UUID
from sqlalchemy import text, Text, Date, DateTime, Integer, func, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from app.models.base import Base

class LinkAnalytics(Base):
    __tablename__ = "link_analytics"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )
    link_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("links.id", ondelete="CASCADE"),
        nullable=False
    )
    date: Mapped[date] = mapped_column(Date, nullable=False)
    views: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    clicks: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    conversions: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    source: Mapped[str] = mapped_column(Text, nullable=False, default="qr")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now()
    )

    # Relationships
    link: Mapped["Link"] = relationship("Link", back_populates="analytics")

    __table_args__ = (
        Index("ix_link_analytics_link_id", "link_id"),
        Index("ix_link_analytics_date", "date"),
        Index("ix_link_analytics_source", "source"),
        UniqueConstraint("link_id", "date", "source", name="uq_link_analytics_link_date_source"),
    )
