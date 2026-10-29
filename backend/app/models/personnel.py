"""
Personnel model — identity info linked 1:1 to users, linked to unit.
This is the bridge between identity (user) and pseudonymous ML data.
"""

import enum
from datetime import datetime, date
from typing import Optional
from beanie import Document, Indexed, PydanticObjectId
from pydantic import Field


class ReviewStatus(str, enum.Enum):
    NEEDS_REVIEW = "needs_review"
    UNDER_REVIEW = "under_review"
    MONITORING = "monitoring"
    INTERVENTION_RECORDED = "intervention_recorded"
    FOLLOW_UP = "follow_up"
    CLOSED = "closed"


class Personnel(Document):
    user_id: Indexed(PydanticObjectId, unique=True)
    unit_id: Indexed(PydanticObjectId)
    service_id: Indexed(str, unique=True)  # force-issued ID
    first_name: str
    last_name: str
    rank: Optional[str] = None
    date_of_joining: Optional[date] = None
    contact_number: Optional[str] = None
    review_status: ReviewStatus = ReviewStatus.CLOSED
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "personnel"
