"""
Intervention — welfare officer's logged actions for a personnel case.
"""

import enum
from datetime import datetime, date
from sqlalchemy import Integer, String, Text, Enum, Date, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class InterventionType(str, enum.Enum):
    COUNSELING = "counseling"
    LEAVE_RECOMMENDATION = "leave_recommendation"
    WORKLOAD_ADJUSTMENT = "workload_adjustment"
    REFERRAL = "referral"
    OTHER = "other"


class InterventionStatus(str, enum.Enum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Intervention(Base):
    __tablename__ = "interventions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    personnel_id: Mapped[int] = mapped_column(Integer, ForeignKey("personnel.id"), nullable=False, index=True)
    welfare_officer_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    risk_prediction_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("risk_predictions.id"), nullable=True)
    intervention_type: Mapped[InterventionType] = mapped_column(Enum(InterventionType), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[InterventionStatus] = mapped_column(Enum(InterventionStatus), default=InterventionStatus.PLANNED)
    follow_up_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    personnel: Mapped["Personnel"] = relationship(back_populates="interventions", foreign_keys=[personnel_id])
    welfare_officer: Mapped["User"] = relationship(foreign_keys=[welfare_officer_id])
