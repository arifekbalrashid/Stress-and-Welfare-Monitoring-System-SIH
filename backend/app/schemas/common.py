"""Common response schemas."""

from pydantic import BaseModel
from typing import Any, Optional


class APIResponse(BaseModel):
    status: str = "success"
    data: Any = None
    message: Optional[str] = None


class PaginatedResponse(BaseModel):
    status: str = "success"
    data: list[Any] = []
    total: int = 0
    page: int = 1
    page_size: int = 20
