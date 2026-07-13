# app/models/menu.py
from datetime import datetime
from typing import List, Optional
from decimal import Decimal
from uuid import UUID, uuid4
from sqlalchemy import text, Text, Integer, Numeric, Boolean, ForeignKey, CheckConstraint, func, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from app.models.base import Base

class Category(Base):
    __tablename__ = "categories"
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    restaurant_id: Mapped[UUID] = mapped_column(ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    restaurant: Mapped["Restaurant"] = relationship(back_populates="categories")
    items: Mapped[List["MenuItem"]] = relationship(back_populates="category")

class MenuItem(Base):
    __tablename__ = "menu_items"
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    restaurant_id: Mapped[UUID] = mapped_column(ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False)
    category_id: Mapped[UUID] = mapped_column(ForeignKey("categories.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    image_url: Mapped[Optional[str]] = mapped_column(Text)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)
    stock_quantity: Mapped[Optional[int]] = mapped_column(Integer)
    low_stock_threshold: Mapped[int] = mapped_column(Integer, default=5)
    preparation_time: Mapped[int] = mapped_column(Integer, default=15, server_default="15") # in minutes
    is_popular: Mapped[bool] = mapped_column(Boolean, default=False)
    calories: Mapped[Optional[int]] = mapped_column(Integer)
    dietary_info: Mapped[Optional[dict]] = mapped_column(JSONB)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    station_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("kitchen_stations.id", ondelete="SET NULL"), nullable=True)
    
    restaurant: Mapped["Restaurant"] = relationship(back_populates="items")
    category: Mapped["Category"] = relationship(back_populates="items")
    modifiers: Mapped[List["MenuItemModifier"]] = relationship(back_populates="item", lazy="selectin")
    station: Mapped[Optional["KitchenStation"]] = relationship(back_populates="menu_items")
    
    __table_args__ = (
        CheckConstraint("price >= 0", name="menu_items_price_check"),
    )

class MenuItemModifier(Base):
    __tablename__ = "menu_item_modifiers"
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    restaurant_id: Mapped[UUID] = mapped_column(ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False)
    menu_item_id: Mapped[UUID] = mapped_column(ForeignKey("menu_items.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0.00)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)
    
    item: Mapped["MenuItem"] = relationship(back_populates="modifiers")
