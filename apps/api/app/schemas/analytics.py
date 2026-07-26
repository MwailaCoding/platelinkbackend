from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import date, datetime
from enum import Enum

class AnalyticsSource(str, Enum):
    QR = "qr"
    DIRECT = "direct"
    WHATSAPP = "whatsapp"
    EMAIL = "email"
    SOCIAL = "social"
    OTHER = "other"

class AnalyticsBase(BaseModel):
    link_id: UUID
    date: date
    views: int = 0
    clicks: int = 0
    conversions: int = 0
    source: AnalyticsSource

class AnalyticsResponse(AnalyticsBase):
    id: UUID
    created_at: datetime

class AnalyticsSummary(BaseModel):
    total_views: int
    total_clicks: int
    total_conversions: int
    ctr: float  # clicks/views * 100
    conversion_rate: float  # conversions/clicks * 100
    source_breakdown: Dict[str, Any]
    daily: List[Dict[str, Any]]
