# app/models/kitchen.py
from datetime import datetime
from typing import List, Optional
from uuid import UUID
from sqlalchemy import text, Integer, Boolean, ForeignKey, DateTime, func, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from app.models.base import Base

class KitchenStation(Base):
    __tablename__ = "kitchen_stations"
    
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    restaurant_id: Mapped[UUID] = mapped_column(ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    display_name: Mapped[Optional[str]] = mapped_column(String(100))
    station_type: Mapped[Optional[str]] = mapped_column(String(50))  # 'hot', 'cold', 'grill', 'fry', 'dessert', 'drinks', 'pastry'
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    restaurant = relationship("Restaurant", back_populates="kitchen_stations")
    prep_times = relationship("StationPrepTime", back_populates="station", cascade="all, delete-orphan")
    routing_rules = relationship("KitchenRoutingRule", foreign_keys="[KitchenRoutingRule.target_station_id]", back_populates="target_station", cascade="all, delete-orphan")
    display_settings = relationship("KitchenDisplaySetting", back_populates="station", cascade="all, delete-orphan")
    staff = relationship("Staff", back_populates="kitchen_station_rel")
    menu_items = relationship("MenuItem", back_populates="station")


class StationPrepTime(Base):
    __tablename__ = "station_prep_times"
    
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    restaurant_id: Mapped[UUID] = mapped_column(ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False)
    station_id: Mapped[UUID] = mapped_column(ForeignKey("kitchen_stations.id", ondelete="CASCADE"), nullable=False)
    item_category: Mapped[str] = mapped_column(String(50), nullable=False)  # 'appetizer', 'main', 'dessert', 'beverage'
    default_seconds: Mapped[int] = mapped_column(Integer, default=600)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    restaurant = relationship("Restaurant")
    station = relationship("KitchenStation", back_populates="prep_times")


class KitchenRoutingRule(Base):
    __tablename__ = "kitchen_routing_rules"
    
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    restaurant_id: Mapped[UUID] = mapped_column(ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False)
    source_station_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("kitchen_stations.id", ondelete="SET NULL"), nullable=True)
    target_station_id: Mapped[UUID] = mapped_column(ForeignKey("kitchen_stations.id", ondelete="CASCADE"), nullable=False)
    item_keyword: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    restaurant = relationship("Restaurant")
    source_station = relationship("KitchenStation", foreign_keys=[source_station_id])
    target_station = relationship("KitchenStation", foreign_keys=[target_station_id], back_populates="routing_rules")


class KitchenDisplaySetting(Base):
    __tablename__ = "kitchen_display_settings"
    
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    restaurant_id: Mapped[UUID] = mapped_column(ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False)
    station_id: Mapped[UUID] = mapped_column(ForeignKey("kitchen_stations.id", ondelete="CASCADE"), nullable=False)
    sound_alerts_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    new_order_volume: Mapped[int] = mapped_column(Integer, default=70)
    ready_order_volume: Mapped[int] = mapped_column(Integer, default=80)
    theme: Mapped[str] = mapped_column(String(20), default="dark")
    font_size: Mapped[str] = mapped_column(String(10), default="large")
    show_timer: Mapped[bool] = mapped_column(Boolean, default=True)
    show_modifiers: Mapped[bool] = mapped_column(Boolean, default=True)
    auto_accept: Mapped[bool] = mapped_column(Boolean, default=False)
    prep_time_buffer_percent: Mapped[int] = mapped_column(Integer, default=10)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    restaurant = relationship("Restaurant")
    station = relationship("KitchenStation", back_populates="display_settings")
