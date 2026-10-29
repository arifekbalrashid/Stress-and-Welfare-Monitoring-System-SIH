"""
Support request — personnel-initiated requests for welfare support.
"""

import enum
from datetime import datetime
from typing import Optional
from beanie import Document, Indexed, PydanticObjectId
from pydantic import Field


class SupportCategory(str, enum.Enum):
    WORKLOAD = "workload"
    PERSONAL = "personal"
    HEALTH = "health"
    LEAVE = "leave"
    DATA_CORRECTION = "data_correction"
    OTHER = "other"


class SupportStatus(str, enum.Enum):
    SUBMITTED = "submitted"
    ACKNOWLEDGED = "acknowledged"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class SupportRequest(Document):
    personnel_id: Indexed(PydanticObjectId)
    category: SupportCategory
    description: str
    status: SupportStatus = SupportStatus.SUBMITTED
    assigned_to: Optional[PydanticObjectId] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "support_requests"
        indexes = ["created_at"]
