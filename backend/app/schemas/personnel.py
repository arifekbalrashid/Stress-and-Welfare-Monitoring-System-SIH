"""Personnel schemas."""

from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional


class PersonnelOut(BaseModel):
    id: int
    service_id: str
    first_name: str
    last_name: str
    rank: Optional[str] = None
    unit_name: Optional[str] = None
    date_of_joining: Optional[date] = None

    class Config:
        from_attributes = True


class PersonnelCreate(BaseModel):
    user_id: int
    unit_id: int
    service_id: str
    first_name: str
    last_name: str
    rank: Optional[str] = None
    date_of_joining: Optional[date] = None
    contact_number: Optional[str] = None
