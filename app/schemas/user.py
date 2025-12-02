"""
User schemas for request/response validation
"""
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID

from app.models.user import UserRole, UserStatus


class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=255)
    role: UserRole = UserRole.VIEWER
    phone: Optional[str] = Field(None, max_length=50)


class UserCreate(UserBase):
    """Schema for creating a user"""
    password: str = Field(..., min_length=8, max_length=100)


class UserUpdate(BaseModel):
    """Schema for updating a user"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None
    phone: Optional[str] = Field(None, max_length=50)
    avatar_url: Optional[str] = None
    password: Optional[str] = Field(None, min_length=8, max_length=100)
    must_change_password: Optional[bool] = None


class UserResponse(UserBase):
    """Schema for user response"""
    id: UUID
    status: UserStatus
    avatar_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime] = None
    must_change_password: bool = False

    model_config = ConfigDict(from_attributes=True)


class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str


class Token(BaseModel):
    """Schema for JWT token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Schema for token payload"""
    user_id: Optional[UUID] = None
    email: Optional[str] = None
