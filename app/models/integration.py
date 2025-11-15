"""
Integration models for external services
"""
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import String, Enum, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB
import uuid
import enum

from app.models.base import Base, SoftDeleteMixin, TimestampMixin


class IntegrationStatus(str, enum.Enum):
    """Integration status enum"""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    PENDING = "pending"


class Integration(Base, TimestampMixin, SoftDeleteMixin):
    """Integration with external services"""
    __tablename__ = "integrations"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255))
    type: Mapped[str] = mapped_column(String(50), index=True)
    status: Mapped[IntegrationStatus] = mapped_column(
        Enum(IntegrationStatus),
        default=IntegrationStatus.DISCONNECTED
    )

    # Encrypted credentials and config stored as JSON
    credentials: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    config: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)

    last_sync_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    def __repr__(self):
        return f"<Integration(id={self.id}, name={self.name}, type={self.type}, status={self.status})>"

