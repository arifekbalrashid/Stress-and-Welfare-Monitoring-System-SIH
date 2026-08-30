"""
User model — login credentials and role assignment.
Identity data is kept here and in personnel; ML-facing data references personnel_id only.
"""

import enum
from datetime import datetime
from sqlalchemy import String, Boolean, Enum, DateTime, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class UserRole(str, enum.Enum):
    PERSONNEL = "personnel"
    WELFARE_OFFICER = "welfare_officer"
    COMMANDER = "commander"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    assigned_unit_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("units.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    personnel: Mapped["Personnel"] = relationship(back_populates="user", uselist=False)
    audit_logs: Mapped[list["AuditLog"]] = relationship(back_populates="actor", foreign_keys="AuditLog.actor_user_id")
    assigned_unit: Mapped["Unit"] = relationship(foreign_keys=[assigned_unit_id])
