"""
Audit log — records sensitive data access (who viewed what, when, why).
"""

from datetime import datetime
from typing import Optional, Any
from beanie import Document, Indexed
from pydantic import Field


class AuditLog(Document):
    actor_user_id: Indexed(Any)
    action: str  # view_case, view_risk, export_data, etc.
    resource_type: str  # risk_prediction, personnel, etc.
    resource_id: Optional[Any] = None
    ip_address: Optional[str] = None
    reason: Optional[str] = None
    created_at: Indexed(datetime, index_type=None) = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "audit_logs"
