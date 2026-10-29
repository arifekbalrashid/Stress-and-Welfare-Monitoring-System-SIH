"""
Intervention — welfare officer's logged actions for a personnel case.
"""

import enum
from datetime import datetime, date
from typing import Optional
from beanie import Document, Indexed, PydanticObjectId
from pydantic import Field


class InterventionType(str, enum.Enum):
    COUNSELING = "counseling"
    LEAVE_RECOMMENDATION = "leave_recommendation"
    WORKLOAD_ADJUSTMENT = "workload_adjustment"
    REFERRAL = "referral"
    OTHER = "other"


class InterventionStatus(str, enum.Enum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Intervention(Document):
    personnel_id: Indexed(PydanticObjectId)
    welfare_officer_id: PydanticObjectId
    risk_prediction_id: Optional[PydanticObjectId] = None
    intervention_type: InterventionType
    notes: Optional[str] = None
    status: InterventionStatus = InterventionStatus.PLANNED
    follow_up_date: Optional[date] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "interventions"
