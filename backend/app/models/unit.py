"""
Unit model — organizational units for Commander aggregation.
"""

from datetime import datetime
from typing import Optional, Any
from beanie import Document, Indexed
from pydantic import Field


class Unit(Document):
    name: Indexed(str, unique=True)
    location: Optional[str] = None
    type: Optional[str] = None  # battalion, company, station, etc.
    commander_user_id: Optional[Any] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "units"
