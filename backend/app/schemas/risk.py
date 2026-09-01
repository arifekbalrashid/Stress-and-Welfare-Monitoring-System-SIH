"""Risk prediction schemas."""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class RiskOut(BaseModel):
    id: int
    risk_score: float
    risk_level: str
    trend: str
    shap_factors: Optional[dict] = None
    confidence: float
    has_wellness_data: bool
    created_at: datetime
    recommendations: list[dict] = []

    class Config:
        from_attributes = True


class PredictRequest(BaseModel):
    personnel_id: int
