"""Validated API and domain models."""
from datetime import datetime, timezone
import unicodedata
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

Priority = Literal["normal", "high", "critical"]


def _has_invisible_format_characters(value: str) -> bool:
    return any(unicodedata.category(character) == "Cf" for character in value)


class CreateJobRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    customer_name: str = Field(min_length=1, max_length=120)
    description: str = Field(min_length=1, max_length=1000)
    priority: Priority = "normal"
    location: str = Field(default="Unspecified", min_length=1, max_length=180)
    technician: str = Field(default="Unassigned", min_length=1, max_length=120)

    @field_validator("customer_name", "description", "location", "technician")
    @classmethod
    def validate_text_fields(cls, value: str) -> str:
        if _has_invisible_format_characters(value):
            raise ValueError("must not contain invisible formatting characters")
        return value


class Job(CreateJobRequest):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid", frozen=True)

    id: int = Field(gt=0)
    status: Literal["open"] = "open"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
