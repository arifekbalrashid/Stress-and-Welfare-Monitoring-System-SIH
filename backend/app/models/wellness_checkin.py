"""
Wellness check-in — voluntary weekly self-reported data (5 questions, 1–5 scale).
"""

from datetime import datetime
from sqlalchemy import Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class WellnessCheckin(Base):
    __tablename__ = "wellness_checkins"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    personnel_id: Mapped[int] = mapped_column(Integer, ForeignKey("personnel.id"), nullable=False, index=True)
    sleep_quality: Mapped[int] = mapped_column(Integer, nullable=False)       # 1–5
    energy_level: Mapped[int] = mapped_column(Integer, nullable=False)        # 1–5
    workload_score: Mapped[int] = mapped_column(Integer, nullable=False)      # 1–5
    wellbeing_score: Mapped[int] = mapped_column(Integer, nullable=False)     # 1–5
    recovery_score: Mapped[int] = mapped_column(Integer, nullable=False)      # 1–5
    # Optional Fields
    sleep_duration: Mapped[float] = mapped_column(Float, nullable=True)       # Optional exact hours
    mood: Mapped[int] = mapped_column(Integer, nullable=True)                 # 1-5
    emotional_exhaustion: Mapped[int] = mapped_column(Integer, nullable=True) # 1-5
    concentration: Mapped[int] = mapped_column(Integer, nullable=True)        # 1-5
    motivation: Mapped[int] = mapped_column(Integer, nullable=True)           # 1-5
    perceived_support: Mapped[int] = mapped_column(Integer, nullable=True)    # 1-5
    physical_exhaustion: Mapped[int] = mapped_column(Integer, nullable=True)  # 1-5
    social_connectedness: Mapped[int] = mapped_column(Integer, nullable=True) # 1-5
    
    submitted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    personnel: Mapped["Personnel"] = relationship(back_populates="wellness_checkins")
