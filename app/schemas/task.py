from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TaskStatusSchema(str, Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"


class TaskCreate(BaseModel):
    """Payload for POST /tasks."""

    title: str = Field(..., min_length=1, max_length=500, strip_whitespace=True)
    description: Optional[str] = Field(None, max_length=50_000)

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("title must not be empty")
        return v.strip()


class TaskStatusUpdate(BaseModel):
    """Payload for PUT /tasks/{id} — status only."""

    status: TaskStatusSchema


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: Optional[str]
    status: TaskStatusSchema
    created_at: datetime


class TaskListResponse(BaseModel):
    """Wrapper for list endpoints."""

    items: list[TaskOut]
    count: int


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorDetail
