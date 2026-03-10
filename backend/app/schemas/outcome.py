from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class OutcomeCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    description: str | None = None
    achieved_at: date | None = None


class OutcomeUpdateRequest(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=300)
    description: str | None = None
    achieved_at: date | None = None


class OutcomeResponse(BaseModel):
    id: UUID
    project_id: UUID
    title: str
    description: str | None
    achieved_at: date | None
    created_by: UUID
    created_at: datetime

    model_config = {"from_attributes": True}
