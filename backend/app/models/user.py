"""
User model — login credentials and role assignment.
Identity data is kept here and in personnel; ML-facing data references personnel_id only.
"""

import enum
from datetime import datetime
from typing import Optional, Any
from beanie import Document, Indexed
from pydantic import Field


class UserRole(str, enum.Enum):
    PERSONNEL = "personnel"
    WELFARE_OFFICER = "welfare_officer"
    COMMANDER = "commander"
    ADMIN = "admin"


class User(Document):
    username: Indexed(str, unique=True)
    email: Indexed(str, unique=True)
    password_hash: str
    role: UserRole
    is_active: bool = True
    assigned_unit_id: Optional[Any] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "users"
