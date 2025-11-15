"""
Client model for customer management
"""
from typing import Optional, List
from decimal import Decimal
from sqlalchemy import String, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
import uuid

from app.models.base import Base, SoftDeleteMixin, TimestampMixin


class Client(Base, TimestampMixin, SoftDeleteMixin):
    """Client/Customer model"""
    __tablename__ = "clients"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), index=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True, index=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    document: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)

    # Address
    address_line1: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    address_line2: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    postal_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    country: Mapped[str] = mapped_column(String(2), default="BR")

    # Client status and metrics
    is_favorite: Mapped[bool] = mapped_column(default=False)
    is_vip: Mapped[bool] = mapped_column(default=False)
    total_shipments: Mapped[int] = mapped_column(default=0)
    total_spent: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"))

    # Foreign keys
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    # Relationships
    responsible_user: Mapped[Optional["User"]] = relationship(
        back_populates="clients",
        foreign_keys=[user_id]
    )
    shipments: Mapped[List["Shipment"]] = relationship(
        back_populates="client",
        foreign_keys="[Shipment.client_id]"
    )
    interactions: Mapped[List["ClientInteraction"]] = relationship(
        back_populates="client",
        foreign_keys="[ClientInteraction.client_id]"
    )

    def __repr__(self):
        return f"<Client(id={self.id}, name={self.name}, email={self.email})>"

