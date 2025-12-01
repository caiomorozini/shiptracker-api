"""
Shipment schemas for request/response validation
"""
from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, List
from datetime import datetime, date
from uuid import UUID
from decimal import Decimal

from app.models.enums import ShipmentStatus


class ShipmentBase(BaseModel):
    """Base shipment schema"""
    tracking_code: Optional[str] = Field(None, max_length=100)
    invoice_number: str = Field(..., min_length=1, max_length=100)
    document: str = Field(..., min_length=11, max_length=18)  # CPF (11) ou CNPJ (14) com formatação
    carrier: str = Field(..., max_length=50)
    status: str = Field(default="pending", max_length=50)
    
    origin_city: Optional[str] = Field(None, max_length=100)
    origin_state: Optional[str] = Field(None, max_length=50)
    origin_country: Optional[str] = Field(None, max_length=2)
    destination_city: Optional[str] = Field(None, max_length=100)
    destination_state: Optional[str] = Field(None, max_length=50)
    destination_country: Optional[str] = Field(None, max_length=2)
    weight_kg: Optional[Decimal] = None
    freight_cost: Optional[Decimal] = None
    declared_value: Optional[Decimal] = None
    description: Optional[str] = None
    estimated_delivery_date: Optional[date] = None
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Valida e normaliza o status do shipment"""
        if not v:
            return "pending"
        
        # Normaliza usando o enum (sempre retorna um valor válido)
        normalized_status = ShipmentStatus.from_string(v)
        return normalized_status.value


class ShipmentCreate(ShipmentBase):
    """Schema for creating a shipment"""
    client_id: Optional[UUID] = None


class ShipmentUpdate(BaseModel):
    """Schema for updating a shipment"""
    tracking_code: Optional[str] = None
    invoice_number: Optional[str] = None
    document: Optional[str] = None
    carrier: Optional[str] = None
    status: Optional[str] = None
    origin_city: Optional[str] = None
    origin_state: Optional[str] = None
    destination_city: Optional[str] = None
    destination_state: Optional[str] = None
    weight_kg: Optional[Decimal] = None
    freight_cost: Optional[Decimal] = None
    declared_value: Optional[Decimal] = None
    description: Optional[str] = None
    estimated_delivery_date: Optional[date] = None
    actual_delivery_date: Optional[date] = None
    client_id: Optional[UUID] = None


class TrackingEventBase(BaseModel):
    """Base tracking event schema"""
    status: str
    description: Optional[str] = None
    location: Optional[str] = None
    occurred_at: datetime
    occurrence_code: Optional[str] = None
    unit: Optional[str] = None
    protocol: Optional[str] = None
    carrier_raw_data: Optional[str] = None
    
    @field_validator('status')
    @classmethod
    def validate_event_status(cls, v: str) -> str:
        """Valida e normaliza o status do evento"""
        if not v:
            return "in_transit"
        
        # Normaliza usando o enum (sempre retorna um valor válido)
        normalized_status = ShipmentStatus.from_string(v)
        return normalized_status.value


class TrackingEventCreate(TrackingEventBase):
    """Schema for creating a tracking event"""
    shipment_id: UUID


class TrackingEventResponse(TrackingEventBase):
    """Schema for tracking event response"""
    id: UUID
    shipment_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ShipmentResponse(ShipmentBase):
    """Schema for shipment response"""
    id: UUID
    client_id: Optional[UUID] = None
    created_by: Optional[UUID] = None
    actual_delivery_date: Optional[date] = None
    created_at: datetime
    updated_at: datetime
    tracking_events: List[TrackingEventResponse] = []

    model_config = ConfigDict(from_attributes=True)


class ShipmentDetailResponse(ShipmentResponse):
    """Schema for detailed shipment response with tracking events"""
    tracking_events: List[TrackingEventResponse] = []

    model_config = ConfigDict(from_attributes=True)


class DashboardFilters(BaseModel):
    """Schema for dashboard filters"""
    search: Optional[str] = None
    statuses: Optional[List[str]] = None
    origin: Optional[str] = None
    destination: Optional[str] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    min_weight: Optional[Decimal] = None
    max_weight: Optional[Decimal] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=100)


class ShipmentStats(BaseModel):
    """Schema for shipment statistics"""
    total_shipments: int
    in_transit: int
    delivered: int
    delayed: int
    cancelled: int


class TrackingTimelineItem(BaseModel):
    """Schema for timeline item (frontend friendly)"""
    id: UUID
    status: str
    description: Optional[str]
    location: Optional[str]
    unit: Optional[str]
    occurrence_code: Optional[str]
    occurred_at: datetime
    is_current: bool = False
    
    model_config = ConfigDict(from_attributes=True)


class TrackingTimeline(BaseModel):
    """Schema for complete tracking timeline"""
    shipment_id: UUID
    tracking_code: Optional[str]
    invoice_number: str
    carrier: str
    current_status: str
    total_events: int
    first_event_date: Optional[datetime]
    last_event_date: Optional[datetime]
    estimated_delivery: Optional[date]
    actual_delivery: Optional[date]
    events: List[TrackingTimelineItem]


class OccurrenceCodeInfo(BaseModel):
    """Schema for occurrence code information"""
    code: str
    description: str
    type: str
    process: str
    
    model_config = ConfigDict(from_attributes=True)


class TrackingEventDetail(TrackingEventResponse):
    """Extended tracking event with occurrence code details"""
    occurrence_code_info: Optional[OccurrenceCodeInfo] = None
    
    model_config = ConfigDict(from_attributes=True)


class TrackingStats(BaseModel):
    """Schema for tracking statistics"""
    total_events: int
    unique_locations: int
    transit_days: Optional[int]
    last_update: Optional[datetime]
    status_history: List[dict]  # [{status: str, count: int, percentage: float}]
