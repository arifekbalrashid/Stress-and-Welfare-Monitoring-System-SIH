"""
Consent — personnel's data sharing consent records.
"""

import enum
from datetime import datetime
from typing import Optional, Any
from beanie import Document, Indexed
from pydantic import Field


class ConsentDataType(str, enum.Enum):
    WELLNESS_CHECKIN = "wellness_checkin"
    OPERATIONAL_VIEW = "operational_view"
    RISK_SHARING = "risk_sharing"


class ConsentStatus(str, enum.Enum):
    GRANTED = "granted"
    WITHDRAWN = "withdrawn"


class Consent(Document):
    personnel_id: Indexed(Any)
    data_type: ConsentDataType
    status: ConsentStatus
    granted_at: Optional[datetime] = None
    withdrawn_at: Optional[datetime] = None

    class Settings:
        name = "consents"
