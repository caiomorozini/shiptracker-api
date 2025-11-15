"""
Common schemas used across the application
"""
from pydantic import BaseModel
from typing import Generic, TypeVar, Optional, List
from datetime import datetime


T = TypeVar('T')


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response schema"""
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int


class MessageResponse(BaseModel):
    """Simple message response schema"""
    message: str
    success: bool = True


class ErrorResponse(BaseModel):
    """Error response schema"""
    error: str
    detail: Optional[str] = None
    timestamp: datetime = datetime.now()


class HealthCheckResponse(BaseModel):
    """Health check response schema"""
    status: str
    timestamp: datetime
    database: str
    redis: str
    mongodb: str
