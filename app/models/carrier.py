"""
Carrier model for shipping companies
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column
import uuid

from app.models.base import Base, TimestampMixin


class Carrier(Base, TimestampMixin):
    """Carrier/Shipping company model"""
    __tablename__ = "carriers"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    color: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, default="#6B7280")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)

    def __repr__(self):
        return f"<Carrier(id={self.id}, name={self.name}, code={self.code})>"
