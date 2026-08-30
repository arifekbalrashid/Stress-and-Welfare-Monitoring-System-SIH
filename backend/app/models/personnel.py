"""
Personnel model — identity info linked 1:1 to users, linked to unit.
This is the bridge between identity (user) and pseudonymous ML data.
"""

import enum
from datetime import datetime, date
from sqlalchemy import String, Integer, Date, DateTime, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class ReviewStatus(str, enum.Enum):
    NEEDS_REVIEW = "needs_review"
    UNDER_REVIEW = "under_review"
    MONITORING = "monitoring"
    INTERVENTION_RECORDED = "intervention_recorded"
    FOLLOW_UP = "follow_up"
    CLOSED = "closed"

class Personnel(Base):
    __tablename__ = "personnel"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    unit_id: Mapped[int] = mapped_column(Integer, ForeignKey("units.id"), nullable=False, index=True)
    service_id: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)  # force-issued ID
    first_name: Mapped[str] = mapped_column(String(60), nullable=False)
    last_name: Mapped[str] = mapped_column(String(60), nullable=False)
    rank: Mapped[str] = mapped_column(String(50), nullable=True)
    date_of_joining: Mapped[date | None] = mapped_column(Date, nullable=True)
    contact_number: Mapped[str | None] = mapped_column(String(15), nullable=True)
    review_status: Mapped[ReviewStatus] = mapped_column(Enum(ReviewStatus), default=ReviewStatus.CLOSED)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="personnel")
    unit: Mapped["Unit"] = relationship(back_populates="personnel_list")
    operational_data: Mapped[list["OperationalData"]] = relationship(back_populates="personnel")
    wellness_checkins: Mapped[list["WellnessCheckin"]] = relationship(back_populates="personnel")
    risk_predictions: Mapped[list["RiskPrediction"]] = relationship(back_populates="personnel")
    interventions: Mapped[list["Intervention"]] = relationship(
        back_populates="personnel", foreign_keys="Intervention.personnel_id"
    )
    consents: Mapped[list["Consent"]] = relationship(back_populates="personnel")
    support_requests: Mapped[list["SupportRequest"]] = relationship(back_populates="personnel")
