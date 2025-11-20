"""
Occurrence Code model for tracking event codes
"""
from typing import Optional
from sqlalchemy import String, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class OccurrenceCode(Base, TimestampMixin):
    """Occurrence Code domain table for delivery tracking events"""
    __tablename__ = "occurrence_codes"
    
    __table_args__ = (
        Index('ix_occurrence_codes_code', 'code', unique=True),
        Index('ix_occurrence_codes_type', 'type'),
        Index('ix_occurrence_codes_process', 'process'),
    )

    code: Mapped[str] = mapped_column(String(10), primary_key=True)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    process: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    def __repr__(self) -> str:
        return f"<OccurrenceCode(code={self.code}, description={self.description})>"
