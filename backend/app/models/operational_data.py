"""
Operational data — admin-imported duty metrics (consolidated table).
"""

from datetime import datetime, date
from sqlalchemy import Integer, Float, String, Date, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class OperationalData(Base):
    __tablename__ = "operational_data"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    personnel_id: Mapped[int] = mapped_column(Integer, ForeignKey("personnel.id"), nullable=False, index=True)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    duty_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    night_shifts: Mapped[int | None] = mapped_column(Integer, nullable=True)
    consecutive_duty_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rest_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    deployment_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    leave_gap_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    training_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    source: Mapped[str] = mapped_column(String(20), default="csv_import")  # csv_import | manual
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    personnel: Mapped["Personnel"] = relationship(back_populates="operational_data")
