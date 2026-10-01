"""Validated API and domain models."""
from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Priority = Literal["normal", "high", "critical"]
SlaStatus = Literal["within_sla", "breached"]


class CreateJobRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    customer_name: str = Field(min_length=1, max_length=120)
    description: str = Field(min_length=1, max_length=1000)
    priority: Priority = "normal"
    location: str = Field(default="Unspecified", min_length=1, max_length=180)
    technician: str = Field(default="Unassigned", min_length=1, max_length=120)


class Job(CreateJobRequest):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid", frozen=True)

    id: int = Field(gt=0)
    status: Literal["open"] = "open"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    sla_status: SlaStatus = "within_sla"
    sla_remaining_seconds: int = 0
