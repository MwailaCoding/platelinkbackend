# app/schemas/kitchen.py
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional, List

# Kitchen Station Schemas
class KitchenStationBase(BaseModel):
    name: str = Field(..., max_length=100)
    display_name: Optional[str] = Field(None, max_length=100)
    station_type: Optional[str] = Field(None, max_length=50)  # 'hot', 'cold', etc.
    display_order: int = 0
    is_active: bool = True

class KitchenStationCreate(KitchenStationBase):
    pass

class KitchenStationUpdate(BaseModel):
    name: Optional[str] = None
    display_name: Optional[str] = None
    station_type: Optional[str] = None
    display_order: Optional[int] = None
    is_active: Optional[bool] = None

class KitchenStationRead(KitchenStationBase):
    id: UUID
    restaurant_id: UUID
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


# Station Prep Time Schemas
class StationPrepTimeBase(BaseModel):
    station_id: UUID
    item_category: str = Field(..., max_length=50)
    default_seconds: int = 600

class StationPrepTimeCreate(StationPrepTimeBase):
    pass

class StationPrepTimeUpdate(BaseModel):
    default_seconds: int

class StationPrepTimeRead(StationPrepTimeBase):
    id: UUID
    restaurant_id: UUID
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


# Kitchen Routing Rule Schemas
class KitchenRoutingRuleBase(BaseModel):
    source_station_id: Optional[UUID] = None
    target_station_id: UUID
    item_keyword: str = Field(..., max_length=100)
    is_active: bool = True

class KitchenRoutingRuleCreate(KitchenRoutingRuleBase):
    pass

class KitchenRoutingRuleRead(KitchenRoutingRuleBase):
    id: UUID
    restaurant_id: UUID
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


# Kitchen Display Settings Schemas
class KitchenDisplaySettingBase(BaseModel):
    sound_alerts_enabled: bool = True
    new_order_volume: int = 70
    ready_order_volume: int = 80
    theme: str = "dark"
    font_size: str = "large"
    show_timer: bool = True
    show_modifiers: bool = True
    auto_accept: bool = False
    prep_time_buffer_percent: int = 10

class KitchenDisplaySettingCreate(KitchenDisplaySettingBase):
    station_id: UUID

class KitchenDisplaySettingUpdate(KitchenDisplaySettingBase):
    pass

class KitchenDisplaySettingRead(KitchenDisplaySettingBase):
    id: UUID
    restaurant_id: UUID
    station_id: UUID
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


# Performance Metrics Schema
class KitchenPerformanceMetrics(BaseModel):
    avg_prep_time_seconds: float
    orders_per_hour: float
    late_orders_count: int
    total_orders_count: int

# Direct Assignment Schemas
class AssignStationRequest(BaseModel):
    station_id: Optional[UUID] = None

class BulkAssignRequest(BaseModel):
    item_ids: List[UUID]
    station_id: Optional[UUID] = None

class HoldRequest(BaseModel):
    reason: str
    resume_at: datetime


