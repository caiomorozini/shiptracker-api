"""
Audit log model for tracking system events
"""
from typing import Optional, Dict, Any
from sqlalchemy import String, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB
import uuid

from app.models.base import Base, TimestampMixin


class AuditLog(Base, TimestampMixin):
    """Audit log for tracking all system events"""
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    event_type: Mapped[str] = mapped_column(String(50), index=True)
    entity_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    entity_id: Mapped[Optional[uuid.UUID]] = mapped_column(nullable=True, index=True)
    
    message: Mapped[str] = mapped_column(Text)
    extra_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    
    # Request metadata
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)    # Relationships
    user: Mapped[Optional["User"]] = relationship(
        back_populates="audit_logs",
        foreign_keys=[user_id]
    )

    def __repr__(self):
        return f"<AuditLog(id={self.id}, event_type={self.event_type}, created_at={self.created_at})>"

