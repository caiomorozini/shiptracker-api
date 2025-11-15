"""
Automation models for business rules and workflows
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import String, ForeignKey, Enum, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB
import uuid
import enum

from app.models.base import Base, SoftDeleteMixin, TimestampMixin


class AutomationStatus(str, enum.Enum):
    """Automation status enum"""
    ACTIVE = "active"
    PAUSED = "paused"


class Automation(Base, TimestampMixin, SoftDeleteMixin):
    """Automation/Workflow model"""
    __tablename__ = "automations"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255))

    # Trigger configuration
    trigger_type: Mapped[str] = mapped_column(String(100))
    trigger_config: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)

    # Action configuration
    action_type: Mapped[str] = mapped_column(String(100))
    action_config: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)

    # Status and metrics
    status: Mapped[AutomationStatus] = mapped_column(
        Enum(AutomationStatus),
        default=AutomationStatus.ACTIVE
    )
    execution_count: Mapped[int] = mapped_column(default=0)
    last_executed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    # Foreign keys
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    # Relationships
    creator: Mapped[Optional["User"]] = relationship(
        back_populates="automations",
        foreign_keys=[created_by]
    )
    executions: Mapped[List["AutomationExecution"]] = relationship(
        back_populates="automation",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Automation(id={self.id}, name={self.name}, status={self.status})>"


class AutomationExecution(Base, TimestampMixin):
    """Automation execution log"""
    __tablename__ = "automation_executions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    automation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("automations.id", ondelete="CASCADE"),
        index=True
    )
    shipment_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("shipments.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    success: Mapped[bool] = mapped_column(default=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    executed_at: Mapped[datetime] = mapped_column()

    # Relationships
    automation: Mapped["Automation"] = relationship(back_populates="executions")

    def __repr__(self):
        return f"<AutomationExecution(id={self.id}, success={self.success}, executed_at={self.executed_at})>"

