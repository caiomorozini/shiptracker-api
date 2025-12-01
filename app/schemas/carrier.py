"""
Carrier schemas for API validation
"""
from typing import Optional
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
import uuid


class CarrierBase(BaseModel):
    """Base carrier schema"""
    name: str = Field(..., min_length=1, max_length=100, description="Carrier name")
    code: str = Field(..., min_length=1, max_length=50, description="Carrier code (unique identifier)")
    color: Optional[str] = Field(default="#6B7280", pattern=r"^#[0-9A-Fa-f]{6}$", description="Hex color code")
    active: bool = Field(default=True, description="Whether the carrier is active")

    @field_validator('code')
    def validate_code(cls, v):
        """Validate and normalize carrier code"""
        return v.lower().strip().replace(' ', '-')


class CarrierCreate(CarrierBase):
    """Schema for creating a new carrier"""
    pass


class CarrierUpdate(BaseModel):
    """Schema for updating a carrier"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    active: Optional[bool] = None

    @field_validator('name')
    def validate_name(cls, v):
        """Validate name if provided"""
        if v is not None:
            return v.strip()
        return v


class CarrierResponse(CarrierBase):
    """Schema for carrier response"""
    id: uuid.UUID
    is_default: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
