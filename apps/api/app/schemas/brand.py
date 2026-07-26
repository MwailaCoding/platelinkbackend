"""Pydantic schemas for restaurant brand customization and themes."""
from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime
from enum import Enum


class CardStyle(str, Enum):
    ROUNDED = "rounded"
    SHARP = "sharp"
    FLOATING = "floating"


class ButtonStyle(str, Enum):
    FILLED = "filled"
    OUTLINE = "outline"
    GHOST = "ghost"


class CategoryDisplay(str, Enum):
    TABS = "tabs"
    DROPDOWN = "dropdown"
    SIDEBAR = "sidebar"


class CartBehavior(str, Enum):
    BOTTOM_BAR = "bottom_bar"
    SIDE_DRAWER = "side_drawer"
    FULL_PAGE = "full_page"


class BrandSettingsBase(BaseModel):
    primary_color: str = Field(default="#F97316", pattern=r"^#[0-9A-Fa-f]{6}$")
    secondary_color: str = Field(default="#0A1628", pattern=r"^#[0-9A-Fa-f]{6}$")
    background_color: str = Field(default="#F8FAFC", pattern=r"^#[0-9A-Fa-f]{6}$")
    text_color: str = Field(default="#0A1628", pattern=r"^#[0-9A-Fa-f]{6}$")
    accent_color: str = Field(default="#10B981", pattern=r"^#[0-9A-Fa-f]{6}$")
    logo_url: Optional[str] = None
    hero_image_url: Optional[str] = None
    favicon_url: Optional[str] = None
    heading_font: str = Field(default="Inter", max_length=100)
    body_font: str = Field(default="Inter", max_length=100)
    welcome_message: Optional[str] = None
    tagline: Optional[str] = Field(None, max_length=255)
    footer_text: Optional[str] = None
    instagram_url: Optional[str] = Field(None, max_length=255)
    facebook_url: Optional[str] = Field(None, max_length=255)
    twitter_url: Optional[str] = Field(None, max_length=255)
    youtube_url: Optional[str] = Field(None, max_length=255)
    card_style: CardStyle = CardStyle.ROUNDED
    button_style: ButtonStyle = ButtonStyle.FILLED
    category_display: CategoryDisplay = CategoryDisplay.TABS
    cart_behavior: CartBehavior = CartBehavior.BOTTOM_BAR
    custom_css: Optional[str] = None
    custom_js: Optional[str] = None
    is_active: bool = True


class BrandSettingsCreate(BrandSettingsBase):
    restaurant_id: UUID


class BrandSettingsUpdate(BaseModel):
    primary_color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    secondary_color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    background_color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    text_color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    accent_color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    logo_url: Optional[str] = None
    hero_image_url: Optional[str] = None
    favicon_url: Optional[str] = None
    heading_font: Optional[str] = Field(None, max_length=100)
    body_font: Optional[str] = Field(None, max_length=100)
    welcome_message: Optional[str] = None
    tagline: Optional[str] = Field(None, max_length=255)
    footer_text: Optional[str] = Field(None)
    instagram_url: Optional[str] = Field(None, max_length=255)
    facebook_url: Optional[str] = Field(None, max_length=255)
    twitter_url: Optional[str] = Field(None, max_length=255)
    youtube_url: Optional[str] = Field(None, max_length=255)
    card_style: Optional[CardStyle] = None
    button_style: Optional[ButtonStyle] = None
    category_display: Optional[CategoryDisplay] = None
    cart_behavior: Optional[CartBehavior] = None
    custom_css: Optional[str] = None
    custom_js: Optional[str] = None
    is_active: Optional[bool] = None


class BrandSettingsResponse(BrandSettingsBase):
    id: UUID
    restaurant_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ThemeBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    preview_image: Optional[str] = None
    template_data: dict
    is_premium: bool = False
    price: float = 0


class ThemeCreate(ThemeBase):
    pass


class ThemeResponse(ThemeBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class ApplyThemeRequest(BaseModel):
    theme_id: UUID


class PreviewResponse(BaseModel):
    css: str
    html: str
    preview_url: str
