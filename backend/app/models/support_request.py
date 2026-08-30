"""
Support request — personnel-initiated requests for welfare support.
"""

import enum
from datetime import datetime
from sqlalchemy import Integer, String, Text, Enum, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class SupportCategory(str, enum.Enum):
    WORKLOAD = "workload"
    PERSONAL = "personal"
    HEALTH = "health"
    LEAVE = "leave"
    DATA_CORRECTION = "data_correction"
    OTHER = "other"


class SupportStatus(str, enum.Enum):
    SUBMITTED = "submitted"
    ACKNOWLEDGED = "acknowledged"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class SupportRequest(Base):
    __tablename__ = "support_requests"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    personnel_id: Mapped[int] = mapped_column(Integer, ForeignKey("personnel.id"), nullable=False, index=True)
    category: Mapped[SupportCategory] = mapped_column(Enum(SupportCategory), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[SupportStatus] = mapped_column(Enum(SupportStatus), default=SupportStatus.SUBMITTED)
    assigned_to: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    personnel: Mapped["Personnel"] = relationship(back_populates="support_requests")
    assigned_officer: Mapped["User"] = relationship(foreign_keys=[assigned_to])
