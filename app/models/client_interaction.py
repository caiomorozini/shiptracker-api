"""
Client interaction model for tracking communications
"""
from typing import Optional, Dict, Any
from sqlalchemy import String, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB
import uuid

from app.models.base import Base, TimestampMixin


class ClientInteraction(Base, TimestampMixin):
    """Client interaction history"""
    __tablename__ = "client_interactions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    client_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("clients.id", ondelete="CASCADE"), 
        index=True
    )
    
    type: Mapped[str] = mapped_column(String(50))
    subject: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)

    # Relationships
    client: Mapped["Client"] = relationship(
        back_populates="interactions", 
        foreign_keys=[client_id]
    )

    def __repr__(self):
        return f"<ClientInteraction(id={self.id}, type={self.type}, client_id={self.client_id})>"

