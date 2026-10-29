"""Common response schemas."""

from typing import Any, Optional
from pydantic import BaseModel, field_validator
from bson import ObjectId


def stringify_object_ids(v: Any) -> Any:
    """Recursively convert bson.ObjectId / PydanticObjectId to string."""
    if isinstance(v, ObjectId):
        return str(v)
    if isinstance(v, dict):
        return {k: stringify_object_ids(val) for k, val in v.items()}
    if isinstance(v, (list, tuple, set)):
        return [stringify_object_ids(item) for item in v]
    return v


class APIResponse(BaseModel):
    status: str = "success"
    data: Any = None
    message: Optional[str] = None

    @field_validator("data", mode="before")
    @classmethod
    def convert_object_ids(cls, v: Any) -> Any:
        return stringify_object_ids(v)


class PaginatedResponse(BaseModel):
    status: str = "success"
    data: list[Any] = []
    total: int = 0
    page: int = 1
    page_size: int = 20

    @field_validator("data", mode="before")
    @classmethod
    def convert_object_ids(cls, v: Any) -> Any:
        return stringify_object_ids(v)
