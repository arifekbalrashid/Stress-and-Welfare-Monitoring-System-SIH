"""
Model version — tracks trained ML models, their metrics, feature set, and deployment status.
"""

import enum
from datetime import datetime
from sqlalchemy import Integer, String, Enum, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class ModelStatus(str, enum.Enum):
    TRAINING = "training"
    ACTIVE = "active"
    ARCHIVED = "archived"


class ModelVersion(Base):
    __tablename__ = "model_versions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    model_type: Mapped[str] = mapped_column(String(50), nullable=False)  # logistic_regression, xgboost
    version_tag: Mapped[str] = mapped_column(String(20), nullable=False)  # v1.0, v1.1
    feature_set_version: Mapped[str] = mapped_column(String(10), nullable=False)  # v1
    metrics: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # precision, recall, f1, auc
    status: Mapped[ModelStatus] = mapped_column(Enum(ModelStatus), default=ModelStatus.TRAINING)
    artifact_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    trained_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    predictions: Mapped[list["RiskPrediction"]] = relationship(back_populates="model_version")
