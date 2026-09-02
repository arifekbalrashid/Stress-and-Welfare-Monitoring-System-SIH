"""Consent schemas."""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ConsentRequest(BaseModel):
    data_type: str  # wellness_checkin, operational_view, risk_sharing


class ConsentOut(BaseModel):
    id: int
    data_type: str
    status: str
    granted_at: Optional[datetime] = None
    withdrawn_at: Optional[datetime] = None

    class Config:
        from_attributes = True
