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
    # 보조 상위 카드 연결 (다중 부모, 최대 개수는 서비스에서 설정값으로 검증)
    linked_parent_ids: list[UUID] = Field(default_factory=list)
    priority: str = Field(default="medium", pattern="^(lowest|low|medium|high|highest)$")
    start_date: date | None = None
    due_date: date | None = None
    column_id: UUID | None = None


class CardUpdateRequest(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=500)
    description: str | None = None
    parent_id: UUID | None = None
    # None이면 변경 없음, 리스트이면 보조 상위 카드 연결을 전체 교체
    linked_parent_ids: list[UUID] | None = None
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


class ParentCardInfo(BaseModel):
    id: UUID
    card_type: str
    card_number: int
    title: str
    # 상위 카드 체인 (예: Task -> Story -> Epic) 표시를 위한 재귀 참조
    parent: "ParentCardInfo | None" = None
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
    column_name: str = ""
    parent: ParentCardInfo | None = None
    # 보조 연결로 노출된 카드 여부 (부모 카드의 sub-cards 목록에서 사용)
    is_linked: bool = False
    assignees: list[CardAssigneeResponse] = []

    @computed_field
    @property
    def display_number(self) -> str:
        return f"{self.prefix}-{self.card_number}" if self.prefix else str(self.card_number)

    model_config = {"from_attributes": True}


class CardWithChildrenResponse(CardResponse):
    children: list[CardResponse] = []

    model_config = {"from_attributes": True}


class CardDetailResponse(CardWithChildrenResponse):
    labels: list[LabelResponse] = []
    comments: list[CommentResponse] = []
    # 보조로 연결된 상위 카드 목록 (다중 부모)
    linked_parents: list[ParentCardInfo] = []

    model_config = {"from_attributes": True}


class CardAssigneeRequest(BaseModel):
    user_id: UUID


class CardReorderRequest(BaseModel):
    parent_id: UUID | None = None
    after_card_id: UUID | None = None  # 이 카드 뒤에 배치 (None이면 첫 번째 위치)
