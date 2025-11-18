"""
Shipment models for package tracking
"""
from datetime import datetime, date
from typing import Optional, List
from decimal import Decimal
from sqlalchemy import String, Date, ForeignKey, Numeric, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
import uuid

from app.models.base import Base, SoftDeleteMixin, TimestampMixin


class Shipment(Base, TimestampMixin, SoftDeleteMixin):
    """Shipment/Package model"""
    __tablename__ = "shipments"
    
    __table_args__ = (
        Index('ix_shipments_document_invoice', 'document', 'invoice_number'),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tracking_code: Mapped[Optional[str]] = mapped_column(String(100), unique=True, nullable=True, index=True)
    invoice_number: Mapped[str] = mapped_column(String(100), index=True)
    document: Mapped[str] = mapped_column(String(50), index=True)  # CPF/CNPJ

    # Foreign keys
    client_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    # Carrier and status
    carrier: Mapped[str] = mapped_column(String(50), index=True)
    status: Mapped[str] = mapped_column(String(50), index=True, default="pending")

    # Origin
    origin_city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    origin_state: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    origin_country: Mapped[Optional[str]] = mapped_column(String(2), nullable=True, default="BR")

    # Destination
    destination_city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    destination_state: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    destination_country: Mapped[Optional[str]] = mapped_column(String(2), nullable=True, default="BR")

    # Package details
    weight_kg: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 2), nullable=True)
    freight_cost: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    declared_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Dates
    estimated_delivery_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    actual_delivery_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Relationships
    client: Mapped[Optional["Client"]] = relationship(
        back_populates="shipments",
        foreign_keys=[client_id]
    )
    creator: Mapped[Optional["User"]] = relationship(
        back_populates="shipments",
        foreign_keys=[created_by]
    )
    tracking_events: Mapped[List["ShipmentTrackingEvent"]] = relationship(
        back_populates="shipment",
        cascade="all, delete-orphan"
    )
    tracking_routine: Mapped[Optional["TrackingRoutine"]] = relationship(
        back_populates="shipment",
        uselist=False,
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Shipment(id={self.id}, tracking_code={self.tracking_code}, status={self.status})>"


class ShipmentTrackingEvent(Base, TimestampMixin):
    """Tracking event history for shipments"""
    __tablename__ = "shipment_tracking_events"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    shipment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("shipments.id", ondelete="CASCADE"),
        index=True
    )

    status: Mapped[str] = mapped_column(String(50))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    occurred_at: Mapped[datetime] = mapped_column()

    # Store raw carrier API response as JSON
    carrier_raw_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    shipment: Mapped["Shipment"] = relationship(back_populates="tracking_events")

    def __repr__(self):
        return f"<ShipmentTrackingEvent(id={self.id}, status={self.status}, occurred_at={self.occurred_at})>"

