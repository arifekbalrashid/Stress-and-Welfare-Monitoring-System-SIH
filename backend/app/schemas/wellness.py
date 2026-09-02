"""Wellness check-in schemas."""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class WellnessCheckinRequest(BaseModel):
    sleep_quality: int = Field(..., ge=1, le=5)
    energy_level: int = Field(..., ge=1, le=5)
    workload_score: int = Field(..., ge=1, le=5)
    wellbeing_score: int = Field(..., ge=1, le=5)
    recovery_score: int = Field(..., ge=1, le=5)
    sleep_duration: Optional[float] = Field(None, ge=0, le=24, description="Optional exact hours of sleep")
    mood: Optional[int] = Field(None, ge=1, le=5)
    emotional_exhaustion: Optional[int] = Field(None, ge=1, le=5)
    concentration: Optional[int] = Field(None, ge=1, le=5)
    motivation: Optional[int] = Field(None, ge=1, le=5)
    perceived_support: Optional[int] = Field(None, ge=1, le=5)
    physical_exhaustion: Optional[int] = Field(None, ge=1, le=5)
    social_connectedness: Optional[int] = Field(None, ge=1, le=5)


class WellnessCheckinOut(BaseModel):
    id: int
    sleep_quality: int
    energy_level: int
    workload_score: int
    wellbeing_score: int
    recovery_score: int
    sleep_duration: Optional[float]
    mood: Optional[int]
    emotional_exhaustion: Optional[int]
    concentration: Optional[int]
    motivation: Optional[int]
    perceived_support: Optional[int]
    physical_exhaustion: Optional[int]
    social_connectedness: Optional[int]
    submitted_at: datetime

    class Config:
        from_attributes = True
