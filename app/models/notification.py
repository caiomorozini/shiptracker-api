"""
Notification model for in-app notifications
"""
from typing import Optional
from sqlalchemy import String, ForeignKey, Enum, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
import uuid
import enum

from app.models.base import Base, TimestampMixin


class NotificationType(str, enum.Enum):
    """Notification type enum"""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


class Notification(Base, TimestampMixin):
    """In-app notification model"""
    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True
    )

    type: Mapped[NotificationType] = mapped_column(
        Enum(NotificationType),
        default=NotificationType.INFO
    )
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    message: Mapped[str] = mapped_column(Text)
    is_read: Mapped[bool] = mapped_column(default=False, index=True)

    # Optional link to entity
    entity_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    entity_id: Mapped[Optional[uuid.UUID]] = mapped_column(nullable=True)

    # Relationships
    user: Mapped["User"] = relationship(
        back_populates="notifications",
        foreign_keys=[user_id]
    )

    def __repr__(self):
        return f"<Notification(id={self.id}, type={self.type}, is_read={self.is_read})>"

