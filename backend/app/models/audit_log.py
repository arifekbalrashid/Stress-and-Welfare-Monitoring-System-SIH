"""
Audit log — records sensitive data access (who viewed what, when, why).
"""

from datetime import datetime
from typing import Optional
from beanie import Document, Indexed, PydanticObjectId
from pydantic import Field


class AuditLog(Document):
    actor_user_id: Indexed(PydanticObjectId)
    action: str  # view_case, view_risk, export_data, etc.
    resource_type: str  # risk_prediction, personnel, etc.
    resource_id: Optional[str] = None
    ip_address: Optional[str] = None
    reason: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "audit_logs"
        indexes = ["created_at"]
