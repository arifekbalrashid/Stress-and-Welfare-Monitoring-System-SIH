"""
Wellness check-in — voluntary weekly self-reported data (5 questions, 1–5 scale).
"""

from datetime import datetime
from typing import Optional
from beanie import Document, Indexed, PydanticObjectId
from pydantic import Field


class WellnessCheckin(Document):
    personnel_id: Indexed(PydanticObjectId)
    sleep_quality: int       # 1–5
    energy_level: int        # 1–5
    workload_score: int      # 1–5
    wellbeing_score: int     # 1–5
    recovery_score: int      # 1–5
    # Optional Fields
    sleep_duration: Optional[float] = None       # Optional exact hours
    mood: Optional[int] = None                   # 1-5
    emotional_exhaustion: Optional[int] = None   # 1-5
    concentration: Optional[int] = None          # 1-5
    motivation: Optional[int] = None             # 1-5
    perceived_support: Optional[int] = None      # 1-5
    physical_exhaustion: Optional[int] = None    # 1-5
    social_connectedness: Optional[int] = None   # 1-5

    submitted_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "wellness_checkins"
        indexes = ["submitted_at"]
