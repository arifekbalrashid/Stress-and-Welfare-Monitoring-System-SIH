"""
Operational data — admin-imported duty metrics (consolidated table).
"""

from datetime import datetime, date
from typing import Optional, Any
from beanie import Document, Indexed
from pydantic import Field


class OperationalData(Document):
    personnel_id: Indexed(Any)
    period_start: date
    period_end: date
    duty_hours: Optional[float] = None
    night_shifts: Optional[int] = None
    consecutive_duty_days: Optional[int] = None
    rest_hours: Optional[float] = None
    deployment_days: Optional[int] = None
    leave_gap_days: Optional[int] = None
    training_hours: Optional[float] = None
    source: str = "csv_import"  # csv_import | manual
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "operational_data"
