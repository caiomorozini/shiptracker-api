"""
This module sets up the declarative base class that other models will inherit from.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all models"""
    pass


class SoftDeleteMixin:
    """Mixin to add soft delete functionality to models"""
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        default=None, 
        nullable=True,
        index=True
    )

    def soft_delete(self):
        """Mark record as deleted"""
        self.deleted_at = func.now()

    def restore(self):
        """Restore a soft-deleted record"""
        self.deleted_at = None

    @property
    def is_deleted(self) -> bool:
        """Check if record is soft-deleted"""
        return self.deleted_at is not None


class TimestampMixin:
    """Mixin to add created_at and updated_at timestamps"""
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )


# Import all models to ensure they are registered with SQLAlchemy
from app.models.user import User, UserRole, UserStatus
from app.models.client import Client
from app.models.shipment import Shipment, ShipmentTrackingEvent
from app.models.tracking_routine import TrackingRoutine, TrackingFrequency
from app.models.automation import Automation, AutomationExecution, AutomationStatus
from app.models.integration import Integration, IntegrationStatus
from app.models.audit_log import AuditLog
from app.models.notification import Notification, NotificationType
from app.models.report import Report
from app.models.client_interaction import ClientInteraction
from app.models.occurrence_code import OccurrenceCode

__all__ = [
    "Base",
    "SoftDeleteMixin",
    "TimestampMixin",
    "User",
    "UserRole",
    "UserStatus",
    "Client",
    "Shipment",
    "ShipmentTrackingEvent",
    "TrackingRoutine",
    "TrackingFrequency",
    "Automation",
    "AutomationExecution",
    "AutomationStatus",
    "Integration",
    "IntegrationStatus",
    "AuditLog",
    "Notification",
    "NotificationType",
    "Report",
    "ClientInteraction",
    "OccurrenceCode",
]

