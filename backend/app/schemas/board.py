from uuid import UUID

from pydantic import BaseModel, Field


class ColumnCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)


class ColumnUpdateRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    wip_limit: int | None = None
    is_end: bool | None = None


class ColumnResponse(BaseModel):
    id: UUID
    project_id: UUID
    name: str
    position: int
    is_end: bool
    wip_limit: int | None

    model_config = {"from_attributes": True}


class ColumnReorderRequest(BaseModel):
    column_ids: list[UUID]


# Forward reference — resolved after CardResponse is defined
from app.schemas.card import CardResponse  # noqa: E402


class ColumnWithCardsResponse(ColumnResponse):
    cards: list[CardResponse] = []

    model_config = {"from_attributes": True}
