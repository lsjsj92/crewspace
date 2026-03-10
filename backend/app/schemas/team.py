from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.auth import UserResponse


class TeamCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None


class TeamUpdateRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None


class TeamResponse(BaseModel):
    id: UUID
    name: str
    description: str | None
    is_active: bool
    created_at: datetime
    member_count: int | None = None

    model_config = {"from_attributes": True}


class AddMemberRequest(BaseModel):
    """팀 멤버 추가 요청 (이메일 기반 사용자 검색)"""
    email: str = Field(..., min_length=1, max_length=255)
    role: str = Field(..., min_length=1)


class UpdateRoleRequest(BaseModel):
    """팀 멤버 역할 변경 요청"""
    role: str = Field(..., min_length=1)


class TeamMemberResponse(BaseModel):
    id: UUID
    user_id: UUID
    role: str
    joined_at: datetime
    user: UserResponse | None = None

    model_config = {"from_attributes": True}


class TeamDetailResponse(BaseModel):
    id: UUID
    name: str
    description: str | None
    is_active: bool
    created_at: datetime
    member_count: int | None = None
    members: list[TeamMemberResponse]

    model_config = {"from_attributes": True}
