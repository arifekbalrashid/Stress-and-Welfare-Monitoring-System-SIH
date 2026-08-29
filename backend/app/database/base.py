"""
SAATHI Backend — SQLAlchemy declarative base.
All ORM models inherit from this Base.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
