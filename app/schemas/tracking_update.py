"""
Schemas for tracking updates (cronjob/bulk operations)
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime

from app.models.enums import ShipmentStatus
from app.core.timezone import make_aware, BRAZIL_TZ


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
    
    @field_validator('occurred_at', mode='before')
    @classmethod
    def validate_occurred_at(cls, v) -> datetime:
        """Garante que occurred_at seja timezone-aware (Brazil timezone)"""
        if isinstance(v, str):
            # Pydantic vai fazer o parse automaticamente
            dt = datetime.fromisoformat(v.replace('Z', '+00:00'))
            return make_aware(dt, BRAZIL_TZ)
        elif isinstance(v, datetime):
            # Se já é datetime, garante que tenha timezone
            return make_aware(v, BRAZIL_TZ)
        return v
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Valida e normaliza o status do evento (scraped data pode vir em português)"""
        if not v:
            return "in_transit"
        
        # Normaliza usando o enum (converte português/malformed para padrão)
        normalized_status = ShipmentStatus.from_string(v)
        return normalized_status.value


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
    
    @field_validator('current_status')
    @classmethod
    def validate_current_status(cls, v: Optional[str]) -> Optional[str]:
        """Valida e normaliza o status atual (scraped data pode vir em português)"""
        if not v:
            return "pending"
        
        # Normaliza usando o enum (converte português/malformed para padrão)
        normalized_status = ShipmentStatus.from_string(v)
        return normalized_status.value


class BulkTrackingUpdate(BaseModel):
    """Schema for bulk tracking updates"""
    shipments: List[ShipmentTrackingUpdate] = Field(..., description="Lista de remessas para atualizar")


class TrackingUpdateResponse(BaseModel):
    """Response for tracking update operations"""
    success: bool
    message: str
    shipment_id: Optional[str] = None
    events_created: int = 0
    events_skipped: int = 0  # Events that already existed (not updated, just skipped)
    errors: List[str] = Field(default_factory=list)


class BulkTrackingUpdateResponse(BaseModel):
    """Response for bulk tracking updates"""
    total_processed: int
    successful: int
    failed: int
    results: List[TrackingUpdateResponse]
