"""
Models package — imports all ORM models so Alembic can discover them.
"""

from app.models.user import User, UserRole
from app.models.unit import Unit
from app.models.personnel import Personnel
from app.models.operational_data import OperationalData
from app.models.wellness_checkin import WellnessCheckin
from app.models.risk_prediction import RiskPrediction, RiskLevel, RiskTrend
from app.models.recommendation import Recommendation
from app.models.intervention import Intervention, InterventionType, InterventionStatus
from app.models.consent import Consent, ConsentDataType, ConsentStatus
from app.models.support_request import SupportRequest, SupportCategory, SupportStatus
from app.models.audit_log import AuditLog
from app.models.model_version import ModelVersion, ModelStatus

__all__ = [
    "User", "UserRole",
    "Unit",
    "Personnel",
    "OperationalData",
    "WellnessCheckin",
    "RiskPrediction", "RiskLevel", "RiskTrend",
    "Recommendation",
    "Intervention", "InterventionType", "InterventionStatus",
    "Consent", "ConsentDataType", "ConsentStatus",
    "SupportRequest", "SupportCategory", "SupportStatus",
    "AuditLog",
    "ModelVersion", "ModelStatus",
]
