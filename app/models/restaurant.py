# app/models/restaurant.py
from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4
from sqlalchemy import text, Text, Boolean, DateTime, func, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, ENUM as PG_ENUM, JSONB
from app.models.base import Base
from app.models.enums import SubscriptionPlan, SubscriptionStatus

class Restaurant(Base):
    __tablename__ = "restaurants"
    
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    name: Mapped[str] = mapped_column(Text, nullable=False)
    slug: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    subdomain: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(Text)
    email: Mapped[Optional[str]] = mapped_column(Text)
    address: Mapped[Optional[str]] = mapped_column(Text)
    logo_url: Mapped[Optional[str]] = mapped_column(Text)
    prefix: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    is_onboarded: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[SubscriptionStatus] = mapped_column(PG_ENUM(SubscriptionStatus, name="subscription_status_enum"), default=SubscriptionStatus.trial)
    subscription_plan: Mapped[SubscriptionPlan] = mapped_column(PG_ENUM(SubscriptionPlan, name="subscription_plan_enum"), default=SubscriptionPlan.starter)
    trial_ends_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    staff: Mapped[List["Staff"]] = relationship(back_populates="restaurant", cascade="all, delete-orphan")
    tables: Mapped[List["Table"]] = relationship(back_populates="restaurant", cascade="all, delete-orphan")
    categories: Mapped[List["Category"]] = relationship(back_populates="restaurant", cascade="all, delete-orphan")
    items: Mapped[List["MenuItem"]] = relationship(back_populates="restaurant", cascade="all, delete-orphan")
    orders: Mapped[List["Order"]] = relationship(back_populates="restaurant", cascade="all, delete-orphan")
    settings: Mapped[List["RestaurantSetting"]] = relationship(back_populates="restaurant", cascade="all, delete-orphan")
    kitchen_stations: Mapped[List["KitchenStation"]] = relationship(back_populates="restaurant", cascade="all, delete-orphan")

class RestaurantSetting(Base):
    __tablename__ = "restaurant_settings"
    restaurant_id: Mapped[UUID] = mapped_column(ForeignKey("restaurants.id", ondelete="CASCADE"), primary_key=True)
    key: Mapped[str] = mapped_column(Text, primary_key=True)
    value: Mapped[dict] = mapped_column(JSONB, nullable=False)
    auto_clear_ready_minutes: Mapped[Optional[int]] = mapped_column(Integer, default=5, server_default="5")
    
    # Pacing settings
    default_pacing: Mapped[str] = mapped_column(Text, default="let_customer_choose", server_default="'let_customer_choose'")
    auto_fire_delay_minutes: Mapped[int] = mapped_column(Integer, default=15, server_default="15")
    
    restaurant: Mapped["Restaurant"] = relationship(back_populates="settings")
