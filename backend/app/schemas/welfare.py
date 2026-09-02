"""Welfare officer schemas."""

from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional


class InterventionCreate(BaseModel):
    personnel_id: int
    risk_prediction_id: Optional[int] = None
    intervention_type: str
    notes: Optional[str] = None
    follow_up_date: Optional[date] = None

class CaseStatusUpdate(BaseModel):
    review_status: str

class SupportRequestStatusUpdate(BaseModel):
    status: str

class InterventionOut(BaseModel):
    id: int
    personnel_id: int
    intervention_type: str
    notes: Optional[str] = None
    status: str
    follow_up_date: Optional[date] = None
    created_at: datetime

    class Config:
        from_attributes = True


class CaseOut(BaseModel):
    personnel_id: int
    service_id: str
    first_name: str
    last_name: str
    rank: Optional[str] = None
    unit_name: Optional[str] = None
    risk_score: Optional[float] = None
    risk_level: Optional[str] = None
    trend: Optional[str] = None
    shap_factors: Optional[dict] = None
    confidence: Optional[float] = None
    has_wellness_data: Optional[bool] = None
    last_prediction_at: Optional[datetime] = None
    recommendations: list[dict] = []
    interventions: list[InterventionOut] = []
