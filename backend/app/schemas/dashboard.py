from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel


class ProjectSummary(BaseModel):
    id: UUID
    name: str
    prefix: str
    status: str
    my_role: str | None = None


class DashboardOverview(BaseModel):
    total_projects: int
    total_active_projects: int
    my_cards_count: int
    projects: list[ProjectSummary]


class CardWithProject(BaseModel):
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
    archived_at: datetime | None
    created_by: UUID
    created_at: datetime
    project_name: str

    model_config = {"from_attributes": True}


class MyCardsResponse(BaseModel):
    cards: list[CardWithProject]


class ColumnCardCount(BaseModel):
    column_id: UUID
    column_name: str
    card_count: int


class ProjectWithCounts(BaseModel):
    id: UUID
    name: str
    prefix: str
    status: str
    columns: list[ColumnCardCount]


class TeamDashboard(BaseModel):
    id: UUID
    name: str
    description: str | None
    projects: list[ProjectWithCounts]
