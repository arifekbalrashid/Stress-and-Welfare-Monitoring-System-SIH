"""
SAATHI Backend — MongoDB connection and initialization using Motor + Beanie.
"""

from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

# Compatibility patch: Motor doesn't directly expose append_metadata on AsyncIOMotorClient,
# which Beanie 2.2+ attempts to call. Delegate to underlying pymongo MongoClient.
if not hasattr(AsyncIOMotorClient, "append_metadata"):
    def _append_metadata(self, *args, **kwargs):
        if hasattr(self.delegate, "append_metadata"):
            return self.delegate.append_metadata(*args, **kwargs)
    AsyncIOMotorClient.append_metadata = _append_metadata

from app.config import get_settings

settings = get_settings()

client = AsyncIOMotorClient(settings.MONGODB_URL)
db = client[settings.MONGODB_DB_NAME]


async def init_db():
    """Initialize Beanie with all document models. Called once at startup."""
    from app.models.user import User
    from app.models.unit import Unit
    from app.models.personnel import Personnel
    from app.models.operational_data import OperationalData
    from app.models.wellness_checkin import WellnessCheckin
    from app.models.risk_prediction import RiskPrediction
    from app.models.recommendation import Recommendation
    from app.models.intervention import Intervention
    from app.models.consent import Consent
    from app.models.support_request import SupportRequest
    from app.models.audit_log import AuditLog
    from app.models.model_version import ModelVersion

    await init_beanie(
        database=db,
        document_models=[
            User,
            Unit,
            Personnel,
            OperationalData,
            WellnessCheckin,
            RiskPrediction,
            Recommendation,
            Intervention,
            Consent,
            SupportRequest,
            AuditLog,
            ModelVersion,
        ],
    )
