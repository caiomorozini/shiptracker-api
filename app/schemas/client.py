"""
Client schemas for request/response validation
"""
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID
from decimal import Decimal


class UserBasic(BaseModel):
    """Basic user info for nested responses"""
    id: UUID
    full_name: str
    email: str

    model_config = ConfigDict(from_attributes=True)


class ClientBase(BaseModel):
    """Base client schema"""
    name: str = Field(..., min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    document: Optional[str] = Field(None, max_length=50)
    address_line1: Optional[str] = Field(None, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=50)
    postal_code: Optional[str] = Field(None, max_length=20)
    country: str = Field(default="BR", max_length=2)


class ClientCreate(ClientBase):
    """Schema for creating a client"""
    user_id: Optional[UUID] = None
    is_favorite: bool = False
    is_vip: bool = False


class ClientUpdate(BaseModel):
    """Schema for updating a client"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    document: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    is_favorite: Optional[bool] = None
    is_vip: Optional[bool] = None
    user_id: Optional[UUID] = None


class ClientResponse(ClientBase):
    """Schema for client response"""
    id: UUID
    is_favorite: bool
    is_vip: bool
    total_shipments: int
    total_spent: Decimal
    user_id: Optional[UUID] = None
    responsible_user: Optional[UserBasic] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ClientStats(BaseModel):
    """Schema for client statistics"""
    total_clients: int
    active_clients: int
    new_this_month: int
    vip_clients: int
