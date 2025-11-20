"""
Occurrence Code schemas for request/response validation
"""
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


class OccurrenceCodeBase(BaseModel):
    """Base occurrence code schema"""
    code: str = Field(..., min_length=1, max_length=10, description="Código da ocorrência")
    description: str = Field(..., min_length=1, max_length=255, description="Descrição da ocorrência")
    type: str = Field(..., min_length=1, max_length=50, description="Tipo da ocorrência (entrega, pendência, etc)")
    process: str = Field(..., min_length=1, max_length=50, description="Processo relacionado (entrega, devolução, etc)")


class OccurrenceCodeCreate(OccurrenceCodeBase):
    """Schema for creating a new occurrence code"""
    pass


class OccurrenceCodeUpdate(BaseModel):
    """Schema for updating an occurrence code"""
    description: str | None = Field(None, min_length=1, max_length=255)
    type: str | None = Field(None, min_length=1, max_length=50)
    process: str | None = Field(None, min_length=1, max_length=50)


class OccurrenceCodeResponse(OccurrenceCodeBase):
    """Schema for occurrence code response"""
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OccurrenceCodeListResponse(BaseModel):
    """Schema for listing occurrence codes"""
    total: int
    items: list[OccurrenceCodeResponse]

    model_config = ConfigDict(from_attributes=True)
