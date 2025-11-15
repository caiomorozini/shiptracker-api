"""
Report model for saved reports and scheduled exports
"""
from typing import Optional, Dict, Any
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB
import uuid

from app.models.base import Base, SoftDeleteMixin, TimestampMixin


class Report(Base, TimestampMixin, SoftDeleteMixin):
    """Saved report configuration"""
    __tablename__ = "reports"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255))
    type: Mapped[str] = mapped_column(String(100))

    # Report filters/configuration
    filters: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)

    # Scheduling
    is_scheduled: Mapped[bool] = mapped_column(default=False)
    schedule_config: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)

    # Foreign keys
    created_by: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE")
    )

    # Relationships
    creator: Mapped["User"] = relationship(
        back_populates="reports",
        foreign_keys=[created_by]
    )

    def __repr__(self):
        return f"<Report(id={self.id}, name={self.name}, type={self.type})>"

