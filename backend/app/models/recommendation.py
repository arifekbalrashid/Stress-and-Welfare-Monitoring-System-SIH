"""
Recommendation — rule-based text suggestions tied to a risk prediction.
"""

from datetime import datetime
from sqlalchemy import Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    risk_prediction_id: Mapped[int] = mapped_column(Integer, ForeignKey("risk_predictions.id"), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)  # workload, rest, leave, support
    recommendation_text: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=1)  # 1 = highest
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    risk_prediction: Mapped["RiskPrediction"] = relationship(back_populates="recommendations")
