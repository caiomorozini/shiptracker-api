"""
Automation schemas for request/response validation
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID

from app.models.automation import AutomationStatus


class AutomationBase(BaseModel):
    """Base automation schema"""
    name: str = Field(..., min_length=1, max_length=255)
    trigger_type: str = Field(..., max_length=100)
    trigger_config: Optional[Dict[str, Any]] = None
    action_type: str = Field(..., max_length=100)
    action_config: Optional[Dict[str, Any]] = None


class AutomationCreate(AutomationBase):
    """Schema for creating an automation"""
    status: AutomationStatus = AutomationStatus.ACTIVE


class AutomationUpdate(BaseModel):
    """Schema for updating an automation"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    trigger_type: Optional[str] = None
    trigger_config: Optional[Dict[str, Any]] = None
    action_type: Optional[str] = None
    action_config: Optional[Dict[str, Any]] = None
    status: Optional[AutomationStatus] = None


class AutomationResponse(AutomationBase):
    """Schema for automation response"""
    id: UUID
    status: AutomationStatus
    execution_count: int
    last_executed_at: Optional[datetime] = None
    created_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AutomationExecutionResponse(BaseModel):
    """Schema for automation execution response"""
    id: UUID
    automation_id: UUID
    shipment_id: Optional[UUID] = None
    success: bool
    error_message: Optional[str] = None
    executed_at: datetime

    model_config = ConfigDict(from_attributes=True)
