"""Validated API and domain models."""
from datetime import datetime, timezone
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

Priority = Literal["normal", "high", "critical"]
Status = Literal["open", "completed"]


class CreateJobRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    customer_name: str = Field(min_length=1, max_length=120)
    description: str = Field(min_length=1, max_length=1000)
    priority: Priority = "normal"
    location: str = Field(default="Unspecified", min_length=1, max_length=180)
    technician: str = Field(default="Unassigned", min_length=1, max_length=120)


class CompleteJobRequest(BaseModel):
    """Operator-supplied context recorded when a job is resolved."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    completion_notes: Optional[str] = Field(default=None, min_length=1, max_length=1000)


class Job(CreateJobRequest):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid", frozen=True)

    id: int = Field(gt=0)
    status: Status = "open"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    completion_notes: Optional[str] = Field(default=None, min_length=1, max_length=1000)
