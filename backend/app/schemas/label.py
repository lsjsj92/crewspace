from uuid import UUID

from pydantic import BaseModel, Field


class LabelCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    color: str = Field(..., pattern="^#[0-9a-fA-F]{6}$")


class LabelUpdateRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    color: str | None = Field(None, pattern="^#[0-9a-fA-F]{6}$")


class LabelResponse(BaseModel):
    id: UUID
    project_id: UUID
    name: str
    color: str

    model_config = {"from_attributes": True}
