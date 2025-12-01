"""
Feedback schemas for request/response validation
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID


class FeedbackBase(BaseModel):
    """Base feedback schema"""
    type: str = Field(..., pattern="^(bug|feature)$", description="Type: 'bug' or 'feature'")
    title: str = Field(..., min_length=5, max_length=200)
    description: str = Field(..., min_length=10)


class FeedbackCreate(FeedbackBase):
    """Schema for creating feedback"""
    pass


class FeedbackUpdate(BaseModel):
    """Schema for updating feedback (admin only)"""
    status: Optional[str] = Field(None, pattern="^(open|in_progress|resolved|closed|duplicate)$")
    priority: Optional[str] = Field(None, pattern="^(low|medium|high|critical)$")
    resolved_at: Optional[datetime] = None


class UserInfo(BaseModel):
    """User information for feedback display"""
    id: UUID
    full_name: str
    avatar_url: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class FeedbackResponse(FeedbackBase):
    """Schema for feedback response"""
    id: UUID
    status: str
    priority: Optional[str] = None
    votes: int
    user_id: Optional[UUID] = None
    user: Optional[UserInfo] = None
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class FeedbackStats(BaseModel):
    """Schema for feedback statistics"""
    total: int
    open: int
    in_progress: int
    resolved: int
    closed: int
    bugs: int
    features: int
    top_voted: list[FeedbackResponse] = []
