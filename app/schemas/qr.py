from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime

class QRDesignData(BaseModel):
    logo_url: Optional[str] = None
    primary_color: str = Field(default="#F97316")
    secondary_color: str = Field(default="#0A1628")
    frame_text: str = Field(default="Scan to Order")
    border_style: str = Field(default="rounded", pattern="^(rounded|sharp|dashed)$")

class QRCodeBase(BaseModel):
    table_number: str
    branch_id: Optional[UUID] = None
    qr_data: QRDesignData
    is_active: bool = True

class QRCodeCreate(QRCodeBase):
    restaurant_id: UUID

class QRCodeUpdate(BaseModel):
    qr_data: Optional[QRDesignData] = None
    is_active: Optional[bool] = None

class QRCodeResponse(QRCodeBase):
    id: UUID
    restaurant_id: UUID
    qr_image_url: Optional[str] = None
    scan_count: int = 0
    order_count: int = 0
    last_scanned: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

class QRDesignRequest(BaseModel):
    table_numbers: List[str]
    design: QRDesignData

class QRDesignResponse(BaseModel):
    qr_codes: List[QRCodeResponse]
    download_url: str
