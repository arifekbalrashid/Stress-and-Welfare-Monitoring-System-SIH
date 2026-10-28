"""
Recommendation — rule-based text suggestions tied to a risk prediction.
"""

from datetime import datetime
from typing import Any
from beanie import Document
from pydantic import Field


class Recommendation(Document):
    risk_prediction_id: Any
    category: str  # workload, rest, leave, support
    recommendation_text: str
    priority: int = 1  # 1 = highest
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "recommendations"
