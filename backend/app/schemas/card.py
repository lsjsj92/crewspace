# backend/app/schemas/card.py
from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field, computed_field

from app.schemas.auth import UserResponse
from app.schemas.label import LabelResponse
from app.schemas.comment import CommentResponse


class CardCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: str | None = None
    card_type: str = Field(..., pattern="^(epic|story|task|sub_task)$")
    parent_id: UUID | None = None
    priority: str = Field(default="medium", pattern="^(lowest|low|medium|high|highest)$")
    start_date: date | None = None
    due_date: date | None = None
    column_id: UUID | None = None


class CardUpdateRequest(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=500)
    description: str | None = None
    parent_id: UUID | None = None
    priority: str | None = Field(None, pattern="^(lowest|low|medium|high|highest)$")
    start_date: date | None = None
    due_date: date | None = None
    cancelled_at: datetime | None = None


class CardMoveRequest(BaseModel):
    column_id: UUID
    position: int


class CardAssigneeResponse(BaseModel):
    id: UUID
    card_id: UUID
    user_id: UUID
    assigned_at: datetime
    user: UserResponse | None = None

    model_config = {"from_attributes": True}


class CardResponse(BaseModel):
    id: UUID
    project_id: UUID
    column_id: UUID
    parent_id: UUID | None
    card_type: str
    card_number: int
    title: str
    description: str | None
    priority: str
    position: int
    start_date: date | None
    due_date: date | None
    completed_at: datetime | None
    cancelled_at: datetime | None = None
    archived_at: datetime | None
    created_by: UUID
    created_at: datetime
    prefix: str = ""
    assignees: list[CardAssigneeResponse] = []

    @computed_field
    @property
    def display_number(self) -> str:
        return f"{self.prefix}-{self.card_number}" if self.prefix else str(self.card_number)

    model_config = {"from_attributes": True}


class ParentCardInfo(BaseModel):
    id: UUID
    card_type: str
    card_number: int
    title: str
    model_config = {"from_attributes": True}


class CardDetailResponse(CardResponse):
    labels: list[LabelResponse] = []
    children: list["CardResponse"] = []
    comments: list[CommentResponse] = []
    parent: ParentCardInfo | None = None

    model_config = {"from_attributes": True}


class CardAssigneeRequest(BaseModel):
    user_id: UUID


class CardReorderRequest(BaseModel):
    parent_id: UUID | None = None
    after_card_id: UUID | None = None  # 이 카드 뒤에 배치 (None이면 첫 번째 위치)
