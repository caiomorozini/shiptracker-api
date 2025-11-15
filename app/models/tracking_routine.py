"""
Tracking routine model for automated shipment checking
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import uuid
import enum

from app.models.base import Base, TimestampMixin


class TrackingFrequency(str, enum.Enum):
    """Tracking frequency enum"""
    HOURLY = "hourly"
    EVERY_6H = "every_6h"
    DAILY = "daily"
    WEEKLY = "weekly"


class TrackingRoutine(Base, TimestampMixin):
    """Tracking routine for automated shipment monitoring"""
    __tablename__ = "tracking_routines"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    shipment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("shipments.id", ondelete="CASCADE"),
        unique=True,
        index=True
    )

    frequency: Mapped[TrackingFrequency] = mapped_column(
        Enum(TrackingFrequency),
        default=TrackingFrequency.DAILY
    )
    notify_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)

    # Scheduling
    last_check_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    next_check_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    # Relationships
    shipment: Mapped["Shipment"] = relationship(back_populates="tracking_routine")

    def __repr__(self):
        return f"<TrackingRoutine(id={self.id}, frequency={self.frequency}, is_active={self.is_active})>"

