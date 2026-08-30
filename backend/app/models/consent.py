"""
Consent — personnel's data sharing consent records.
"""

import enum
from datetime import datetime
from sqlalchemy import Integer, String, Enum, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class ConsentDataType(str, enum.Enum):
    WELLNESS_CHECKIN = "wellness_checkin"
    OPERATIONAL_VIEW = "operational_view"
    RISK_SHARING = "risk_sharing"


class ConsentStatus(str, enum.Enum):
    GRANTED = "granted"
    WITHDRAWN = "withdrawn"


class Consent(Base):
    __tablename__ = "consents"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    personnel_id: Mapped[int] = mapped_column(Integer, ForeignKey("personnel.id"), nullable=False, index=True)
    data_type: Mapped[ConsentDataType] = mapped_column(Enum(ConsentDataType), nullable=False)
    status: Mapped[ConsentStatus] = mapped_column(Enum(ConsentStatus), nullable=False)
    granted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    withdrawn_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationships
    personnel: Mapped["Personnel"] = relationship(back_populates="consents")
