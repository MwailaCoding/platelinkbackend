"""Onboarding Pydantic Schemas."""
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

class OnboardingStepEnum(str, Enum):
    ACCOUNT_CREATION = "account_creation"
    EMAIL_VERIFICATION = "email_verification"
    BUSINESS_PROFILE = "business_profile"
    BRANCH_CONFIG = "branch_config"
    BRAND_CUSTOMIZATION = "brand_customization"
    MENU_SETUP = "menu_setup"
    FLOOR_PLAN = "floor_plan"
    PAYMENT_SETUP = "payment_setup"
    STAFF_INVITES = "staff_invites"
    COMPLETE = "complete"

class RestaurantSizeEnum(str, Enum):
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    ENTERPRISE = "enterprise"

class RestaurantTypeEnum(str, Enum):
    FAST_FOOD = "fast_food"
    CASUAL_DINING = "casual_dining"
    FINE_DINING = "fine_dining"
    CAFE = "cafe"
    BAR_LOUNGE = "bar_lounge"
    HOTEL_RESTAURANT = "hotel_restaurant"
    FOOD_TRUCK = "food_truck"
    CATERING = "catering"
    GHOST_KITCHEN = "ghost_kitchen"

class OnboardingStatusResponse(BaseModel):
    id: UUID
    restaurant_id: UUID
    step_completed: List[str]
    is_complete: bool
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class BrandSettingsBase(BaseModel):
    logo_url: Optional[str] = None
    hero_image_url: Optional[str] = None
    primary_color: str = Field("#F97316", pattern=r"^#[0-9a-fA-F]{6}$")
    secondary_color: str = Field("#0A1628", pattern=r"^#[0-9a-fA-F]{6}$")
    theme_id: Optional[UUID] = None
    custom_css: Optional[str] = None

class BrandSettingsCreate(BrandSettingsBase):
    pass

class BrandSettingsUpdate(BaseModel):
    logo_url: Optional[str] = None
    hero_image_url: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    theme_id: Optional[UUID] = None
    custom_css: Optional[str] = None

class BrandSettingsResponse(BrandSettingsBase):
    id: UUID
    restaurant_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class RestaurantConfigUpdate(BaseModel):
    size: Optional[RestaurantSizeEnum] = None
    type: Optional[RestaurantTypeEnum] = None
    is_multi_branch: Optional[bool] = None
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None

class RestaurantConfigResponse(BaseModel):
    restaurant_id: UUID
    size: str
    type: Optional[str] = None
    is_multi_branch: bool
    logo_url: Optional[str] = None
    primary_color: str

    model_config = ConfigDict(from_attributes=True)

class OnboardingCompleteResponse(BaseModel):
    restaurant_id: UUID
    slug: str
    primary_link: str
    branch_links: List[Dict[str, str]]
    qr_download_url: str
    dashboard_url: str
    staff_invite_summary: Dict[str, Any]
