"""
User model for authentication and authorization
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Enum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
import uuid
import enum

from app.models.base import Base, SoftDeleteMixin, TimestampMixin


class UserRole(str, enum.Enum):
    """User roles enum"""
    ADMIN = "ADMIN"
    MANAGER = "MANAGER"
    OPERATOR = "OPERATOR"
    SELLER = "SELLER"
    VIEWER = "VIEWER"


class UserStatus(str, enum.Enum):
    """User status enum"""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class User(Base, TimestampMixin, SoftDeleteMixin):
    """User model for team members"""
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.VIEWER)
    status: Mapped[UserStatus] = mapped_column(Enum(UserStatus), default=UserStatus.ACTIVE)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    # Relationships
    clients: Mapped[List["Client"]] = relationship(
        back_populates="responsible_user",
        foreign_keys="[Client.user_id]"
    )
    shipments: Mapped[List["Shipment"]] = relationship(
        back_populates="creator",
        foreign_keys="[Shipment.created_by]"
    )
    automations: Mapped[List["Automation"]] = relationship(
        back_populates="creator",
        foreign_keys="[Automation.created_by]"
    )
    reports: Mapped[List["Report"]] = relationship(
        back_populates="creator",
        foreign_keys="[Report.created_by]"
    )
    audit_logs: Mapped[List["AuditLog"]] = relationship(
        back_populates="user",
        foreign_keys="[AuditLog.user_id]"
    )
    notifications: Mapped[List["Notification"]] = relationship(
        back_populates="user",
        foreign_keys="[Notification.user_id]"
    )
    feedbacks: Mapped[List["Feedback"]] = relationship(
        back_populates="user",
        foreign_keys="[Feedback.user_id]"
    )

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"

