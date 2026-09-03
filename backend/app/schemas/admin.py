"""Admin schemas."""

from pydantic import BaseModel, EmailStr
from datetime import date
from typing import Optional


class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    role: str
    assigned_unit_id: Optional[int] = None


class UserUpdate(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    assigned_unit_id: Optional[int] = None


class UnitCreate(BaseModel):
    name: str
    location: Optional[str] = None
    type: Optional[str] = None
    commander_user_id: Optional[int] = None


class UnitOut(BaseModel):
    id: int
    name: str
    location: Optional[str] = None
    type: Optional[str] = None
    personnel_count: int = 0

    class Config:
        from_attributes = True


class SupportRequestCreate(BaseModel):
    category: str
    description: str = ""


class SupportRequestOut(BaseModel):
    id: int
    category: str
    description: str
    status: str
    created_at: object

    class Config:
        from_attributes = True
