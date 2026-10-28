"""
Risk prediction — model output stored per personnel per prediction run.
"""

import enum
from datetime import datetime
from typing import Optional, Any
from beanie import Document, Indexed
from pydantic import Field


class RiskLevel(str, enum.Enum):
    LOW = "low"
    MODERATE = "moderate"
    ELEVATED = "elevated"
    HIGH = "high"


class RiskTrend(str, enum.Enum):
    INCREASING = "increasing"
    STABLE = "stable"
    DECREASING = "decreasing"


class RiskPrediction(Document):
    personnel_id: Indexed(Any)
    risk_score: float  # 0–100
    risk_level: Indexed(RiskLevel)
    trend: RiskTrend
    shap_factors: Optional[dict] = None  # top contributing factors
    confidence: float = 1.0
    model_version_id: Optional[Any] = None
    has_wellness_data: bool = True
    created_at: Indexed(datetime, index_type=None) = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "risk_predictions"
