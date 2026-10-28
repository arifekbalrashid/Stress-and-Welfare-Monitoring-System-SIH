"""
Model version — tracks trained ML models, their metrics, feature set, and deployment status.
"""

import enum
from datetime import datetime
from typing import Optional
from beanie import Document
from pydantic import Field


class ModelStatus(str, enum.Enum):
    TRAINING = "training"
    ACTIVE = "active"
    ARCHIVED = "archived"


class ModelVersion(Document):
    model_type: str  # logistic_regression, xgboost
    version_tag: str  # v1.0, v1.1
    feature_set_version: str  # v1
    metrics: Optional[dict] = None  # precision, recall, f1, auc
    status: ModelStatus = ModelStatus.TRAINING
    artifact_path: Optional[str] = None
    trained_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "model_versions"
