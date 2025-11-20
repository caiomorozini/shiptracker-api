"""
Schemas for tracking updates (cronjob/bulk operations)
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class TrackingEventData(BaseModel):
    """Schema for a single tracking event data from scraper"""
    occurrence_code: Optional[str] = Field(None, description="Código da ocorrência")
    status: str = Field(..., description="Status do evento")
    description: Optional[str] = Field(None, description="Descrição detalhada")
    location: Optional[str] = Field(None, description="Localização (cidade/estado)")
    unit: Optional[str] = Field(None, description="Unidade operacional")
    occurred_at: datetime = Field(..., description="Data/hora do evento")
    protocol: Optional[str] = Field(None, description="Protocolo SEFAZ ou similar")
    raw_data: Optional[str] = Field(None, description="Dados brutos do HTML/API")


class ShipmentTrackingUpdate(BaseModel):
    """Schema for updating shipment tracking from cronjob"""
    tracking_code: Optional[str] = Field(None, description="Código de rastreamento")
    invoice_number: str = Field(..., description="Número da nota fiscal")
    document: str = Field(..., description="CPF/CNPJ do destinatário")
    carrier: str = Field(default="SSW", description="Transportadora")
    
    # Current status
    current_status: Optional[str] = Field(None, description="Status atual do envio")
    
    # Tracking events
    events: List[TrackingEventData] = Field(default_factory=list, description="Lista de eventos de rastreamento")
    
    # Additional metadata
    last_update: Optional[datetime] = Field(None, description="Última atualização")


class BulkTrackingUpdate(BaseModel):
    """Schema for bulk tracking updates"""
    shipments: List[ShipmentTrackingUpdate] = Field(..., description="Lista de remessas para atualizar")


class TrackingUpdateResponse(BaseModel):
    """Response for tracking update operations"""
    success: bool
    message: str
    shipment_id: Optional[str] = None
    events_created: int = 0
    events_updated: int = 0
    errors: List[str] = Field(default_factory=list)


class BulkTrackingUpdateResponse(BaseModel):
    """Response for bulk tracking updates"""
    total_processed: int
    successful: int
    failed: int
    results: List[TrackingUpdateResponse]
