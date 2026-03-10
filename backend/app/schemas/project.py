from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.auth import UserResponse


class ProjectCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=300)
    description: str | None = None
    prefix: str = Field(..., min_length=1, max_length=10)
    start_date: date | None = None
    end_date: date | None = None
    manager_user_id: UUID | None = None


class ProjectUpdateRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=300)
    description: str | None = None
    start_date: date | None = None
    end_date: date | None = None


class BoardColumnResponse(BaseModel):
    id: UUID
    name: str
    position: int
    is_end: bool
    wip_limit: int | None

    model_config = {"from_attributes": True}


class ProjectMemberResponse(BaseModel):
    id: UUID
    project_id: UUID
    user_id: UUID
    role: str
    joined_at: datetime
    user: UserResponse | None = None

    model_config = {"from_attributes": True}


class ProjectResponse(BaseModel):
    id: UUID
    team_id: UUID | None = None
    name: str
    description: str | None
    prefix: str
    status: str
    start_date: date | None
    end_date: date | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ProjectDetailResponse(BaseModel):
    id: UUID
    team_id: UUID | None = None
    name: str
    description: str | None
    prefix: str
    status: str
    start_date: date | None
    end_date: date | None
    created_at: datetime
    columns: list[BoardColumnResponse]

    model_config = {"from_attributes": True}


class AddProjectMemberRequest(BaseModel):
    user_id: UUID
    role: str = Field(..., pattern="^(manager|member|viewer)$")


class UpdateProjectMemberRoleRequest(BaseModel):
    role: str = Field(..., pattern="^(manager|member|viewer)$")
