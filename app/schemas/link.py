from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from enum import Enum

class LinkType(str, Enum):
    PRIMARY = "primary"
    MENU = "menu"
    ORDER = "order"
    ADMIN = "admin"
    WAITER = "waiter"
    KITCHEN = "kitchen"
    CASHIER = "cashier"
    CUSTOM = "custom"

class LinkBase(BaseModel):
    type: LinkType
    slug: str = Field(..., min_length=3, max_length=50, pattern="^[a-z0-9-]+$")
    branch_id: Optional[UUID] = None
    is_active: bool = True

class LinkCreate(LinkBase):
    restaurant_id: UUID
    custom_domain: Optional[str] = None

class LinkUpdate(BaseModel):
    slug: Optional[str] = Field(None, min_length=3, max_length=50)
    custom_domain: Optional[str] = None
    domain_verified: Optional[bool] = None
    is_active: Optional[bool] = None

class LinkResponse(LinkBase):
    id: UUID
    restaurant_id: UUID
    url: str
    custom_domain: Optional[str] = None
    domain_verified: bool = False
    created_at: datetime
    updated_at: datetime

class CustomDomainRequest(BaseModel):
    domain: str = Field(..., pattern=r"^([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}$")

class CustomDomainResponse(BaseModel):
    domain: str
    verified: bool
    dns_record: str
    status: str  # pending, verified, failed

class StaffAccessLinks(BaseModel):
    waiter: str
    kitchen: str
    cashier: str
