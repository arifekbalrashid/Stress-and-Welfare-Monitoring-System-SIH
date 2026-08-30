"""
Risk prediction — model output stored per personnel per prediction run.
"""

import enum
from datetime import datetime
from sqlalchemy import Integer, Float, String, Enum, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class RiskLevel(str, enum.Enum):
    LOW = "low"
    MODERATE = "moderate"
    ELEVATED = "elevated"
    HIGH = "high"


class RiskTrend(str, enum.Enum):
    INCREASING = "increasing"
    STABLE = "stable"
    DECREASING = "decreasing"


class RiskPrediction(Base):
    __tablename__ = "risk_predictions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    personnel_id: Mapped[int] = mapped_column(Integer, ForeignKey("personnel.id"), nullable=False, index=True)
    risk_score: Mapped[float] = mapped_column(Float, nullable=False)  # 0–100
    risk_level: Mapped[RiskLevel] = mapped_column(Enum(RiskLevel), nullable=False, index=True)
    trend: Mapped[RiskTrend] = mapped_column(Enum(RiskTrend), nullable=False)
    shap_factors: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # top contributing factors
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    model_version_id: Mapped[int] = mapped_column(Integer, ForeignKey("model_versions.id"), nullable=False)
    has_wellness_data: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    personnel: Mapped["Personnel"] = relationship(back_populates="risk_predictions")
    model_version: Mapped["ModelVersion"] = relationship(back_populates="predictions")
    recommendations: Mapped[list["Recommendation"]] = relationship(back_populates="risk_prediction")
