# backend/app/api/v1/teams.py
# 팀 관련 API 엔드포인트 (팀 CRUD, 멤버 관리)
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.database import get_db
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.team import (
    AddMemberRequest,
    TeamCreateRequest,
    TeamDetailResponse,
    TeamMemberResponse,
    TeamResponse,
    TeamUpdateRequest,
    UpdateRoleRequest,
)
from app.services import team_service

router = APIRouter()


@router.get("", response_model=list[TeamResponse])
async def list_my_teams(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[TeamResponse]:
    """현재 사용자가 속한 팀 목록을 반환한다."""
    return await team_service.get_user_teams(db, current_user.id)


@router.post("", response_model=TeamResponse, status_code=201)
async def create_team(
    data: TeamCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> TeamResponse:
    """새 팀을 생성한다."""
    return await team_service.create_team(db, data, current_user)


@router.get("/{team_id}", response_model=TeamDetailResponse)
async def get_team(
    team_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> TeamDetailResponse:
    """팀 상세 정보를 멤버 목록과 함께 반환한다."""
    return await team_service.get_team(db, team_id)


@router.patch("/{team_id}", response_model=TeamResponse)
async def update_team(
    team_id: UUID,
    data: TeamUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> TeamResponse:
    """팀 정보를 수정한다."""
    return await team_service.update_team(db, team_id, data, current_user)


@router.delete("/{team_id}", response_model=MessageResponse)
async def delete_team(
    team_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> MessageResponse:
    """팀을 소프트 삭제한다."""
    await team_service.delete_team(db, team_id, current_user)
    return MessageResponse(message="Team deleted successfully")


@router.get("/{team_id}/members", response_model=list[TeamMemberResponse])
async def list_team_members(
    team_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[TeamMemberResponse]:
    """팀의 멤버 목록을 반환한다."""
    return await team_service.get_members(db, team_id)


@router.post("/{team_id}/members", response_model=TeamMemberResponse, status_code=201)
async def add_team_member(
    team_id: UUID,
    data: AddMemberRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> TeamMemberResponse:
    """이메일로 사용자를 검색하여 팀에 추가한다."""
    return await team_service.add_member(db, team_id, data, current_user)


@router.patch("/{team_id}/members/{user_id}", response_model=TeamMemberResponse)
async def update_member_role(
    team_id: UUID,
    user_id: UUID,
    data: UpdateRoleRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> TeamMemberResponse:
    """팀 멤버의 역할을 변경한다."""
    return await team_service.update_member_role(db, team_id, user_id, data, current_user)


@router.delete("/{team_id}/members/{user_id}", response_model=MessageResponse)
async def remove_team_member(
    team_id: UUID,
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> MessageResponse:
    """팀에서 멤버를 제거한다."""
    await team_service.remove_member(db, team_id, user_id, current_user)
    return MessageResponse(message="Member removed successfully")
