"""
Feedback model for bug reports and feature suggestions
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, Text, ForeignKey, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
import uuid

from app.models.base import Base, TimestampMixin


class Feedback(Base, TimestampMixin):
    """Feedback model for user bug reports and feature suggestions"""
    __tablename__ = "feedback"
    
    __table_args__ = (
        Index('ix_feedback_type_status', 'type', 'status'),
        Index('ix_feedback_votes', 'votes'),
        Index('ix_feedback_created_at', 'created_at'),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    
    # Type: 'bug' or 'feature'
    type: Mapped[str] = mapped_column(String(20), index=True)
    
    # Content
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    
    # Status: 'open', 'in_progress', 'resolved', 'closed', 'duplicate'
    status: Mapped[str] = mapped_column(String(20), default="open", index=True)
    
    # Priority: 'low', 'medium', 'high', 'critical' (set by admins)
    priority: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    # Voting system
    votes: Mapped[int] = mapped_column(Integer, default=0)
    
    # User who created the feedback
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Resolution date
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user: Mapped[Optional["User"]] = relationship(back_populates="feedbacks")

    def __repr__(self):
        return f"<Feedback(id={self.id}, type={self.type}, title={self.title[:30]})>"
