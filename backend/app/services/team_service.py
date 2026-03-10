# backend/app/services/team_service.py
# 팀 관련 비즈니스 로직 (팀 CRUD, 멤버 관리, 권한 검증)
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.base import (
    BadRequestException,
    ForbiddenException,
    NotFoundException,
)
from app.models.team import Team, TeamMember, TeamRole
from app.models.user import User
from app.repositories.team_repository import TeamRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import UserResponse
from app.schemas.team import (
    AddMemberRequest,
    TeamCreateRequest,
    TeamDetailResponse,
    TeamMemberResponse,
    TeamResponse,
    TeamUpdateRequest,
    UpdateRoleRequest,
)


def _team_response(team: Team) -> TeamResponse:
    """Team 모델을 TeamResponse로 변환한다."""
    return TeamResponse(
        id=team.id,
        name=team.name,
        description=team.description,
        is_active=team.is_active,
        created_at=team.created_at,
        member_count=len(team.members) if team.members else 0,
    )


def _member_response(member: TeamMember) -> TeamMemberResponse:
    """TeamMember 모델을 TeamMemberResponse로 변환한다."""
    user_resp = UserResponse.model_validate(member.user) if member.user else None
    return TeamMemberResponse(
        id=member.id,
        user_id=member.user_id,
        role=member.role.value,
        joined_at=member.joined_at,
        user=user_resp,
    )


async def check_team_permission(
    db: AsyncSession,
    team_id: UUID,
    user_id: UUID,
    required_roles: list[str],
) -> TeamMember:
    """사용자의 팀 역할을 검증한다. 필요한 역할이 없으면 ForbiddenException을 발생시킨다."""
    team_repo = TeamRepository(db)
    member = await team_repo.get_member(team_id, user_id)
    if not member:
        raise ForbiddenException(detail="Not a member of this team")
    if member.role.value not in required_roles:
        raise ForbiddenException(detail="Insufficient team role")
    return member


async def create_team(
    db: AsyncSession, data: TeamCreateRequest, current_user: User
) -> TeamResponse:
    """새 팀을 생성하고 생성자를 소유자로 추가한다."""
    team_repo = TeamRepository(db)
    team = await team_repo.create(
        name=data.name,
        description=data.description,
        created_by=current_user.id,
    )
    # 생성자를 소유자(owner)로 추가
    await team_repo.add_member(team.id, current_user.id, TeamRole.owner)
    # 멤버 관계를 포함하여 다시 조회
    team = await team_repo.get_by_id(team.id)
    return _team_response(team)


async def get_user_teams(db: AsyncSession, user_id: UUID) -> list[TeamResponse]:
    """사용자가 속한 모든 팀을 반환한다."""
    team_repo = TeamRepository(db)
    teams = await team_repo.get_user_teams(user_id)
    return [_team_response(t) for t in teams]


async def get_team(db: AsyncSession, team_id: UUID) -> TeamDetailResponse:
    """팀 상세 정보를 멤버 목록과 함께 반환한다."""
    team_repo = TeamRepository(db)
    team = await team_repo.get_by_id(team_id)
    if not team or team.deleted_at is not None:
        raise NotFoundException(detail="Team not found")

    members = await team_repo.get_team_members(team_id)
    return TeamDetailResponse(
        id=team.id,
        name=team.name,
        description=team.description,
        is_active=team.is_active,
        created_at=team.created_at,
        member_count=len(members),
        members=[_member_response(m) for m in members],
    )


async def update_team(
    db: AsyncSession, team_id: UUID, data: TeamUpdateRequest, current_user: User
) -> TeamResponse:
    """팀 정보를 수정한다. owner 또는 manager 역할이 필요하다."""
    await check_team_permission(db, team_id, current_user.id, ["owner", "manager"])
    team_repo = TeamRepository(db)
    update_data = data.model_dump(exclude_unset=True)
    if update_data:
        team = await team_repo.update(team_id, **update_data)
    else:
        team = await team_repo.get_by_id(team_id)
    if not team:
        raise NotFoundException(detail="Team not found")
    return _team_response(team)


async def delete_team(
    db: AsyncSession, team_id: UUID, current_user: User
) -> None:
    """팀을 소프트 삭제한다. owner 역할 또는 superadmin 권한이 필요하다."""
    if not current_user.is_superadmin:
        await check_team_permission(db, team_id, current_user.id, ["owner"])
    team_repo = TeamRepository(db)
    deleted = await team_repo.soft_delete(team_id)
    if not deleted:
        raise NotFoundException(detail="Team not found")


async def get_members(db: AsyncSession, team_id: UUID) -> list[TeamMemberResponse]:
    """팀의 전체 멤버 목록을 반환한다."""
    team_repo = TeamRepository(db)
    team = await team_repo.get_by_id(team_id)
    if not team or team.deleted_at is not None:
        raise NotFoundException(detail="Team not found")
    members = await team_repo.get_team_members(team_id)
    return [_member_response(m) for m in members]


async def add_member(
    db: AsyncSession,
    team_id: UUID,
    data: AddMemberRequest,
    current_user: User,
) -> TeamMemberResponse:
    """이메일로 사용자를 검색하여 팀에 추가한다. owner 또는 manager 역할이 필요하다."""
    await check_team_permission(db, team_id, current_user.id, ["owner", "manager"])

    team_repo = TeamRepository(db)

    # 팀 존재 여부 확인
    team = await team_repo.get_by_id(team_id)
    if not team or team.deleted_at is not None:
        raise NotFoundException(detail="Team not found")

    # 이메일로 대상 사용자 검색
    user_repo = UserRepository(db)
    target_user = await user_repo.get_by_email(data.email)
    if not target_user:
        raise NotFoundException(detail="User not found with this email")

    # 이미 멤버인지 확인
    existing = await team_repo.get_member(team_id, target_user.id)
    if existing:
        raise BadRequestException(detail="User is already a member of this team")

    try:
        role = TeamRole(data.role)
    except ValueError:
        raise BadRequestException(detail=f"Invalid role: {data.role}")

    member = await team_repo.add_member(team_id, target_user.id, role)
    # 사용자 관계를 포함하여 다시 조회
    member = await team_repo.get_member(team_id, target_user.id)
    return _member_response(member)


async def update_member_role(
    db: AsyncSession,
    team_id: UUID,
    user_id: UUID,
    data: UpdateRoleRequest,
    current_user: User,
) -> TeamMemberResponse:
    """팀 멤버의 역할을 변경한다. owner 또는 manager 역할이 필요하다."""
    await check_team_permission(db, team_id, current_user.id, ["owner", "manager"])

    team_repo = TeamRepository(db)
    existing = await team_repo.get_member(team_id, user_id)
    if not existing:
        raise NotFoundException(detail="Team member not found")

    try:
        role = TeamRole(data.role)
    except ValueError:
        raise BadRequestException(detail=f"Invalid role: {data.role}")

    member = await team_repo.update_member_role(team_id, user_id, role)
    return _member_response(member)


async def remove_member(
    db: AsyncSession,
    team_id: UUID,
    user_id: UUID,
    current_user: User,
) -> None:
    """팀에서 멤버를 제거한다. owner 또는 manager 역할이 필요하다."""
    await check_team_permission(db, team_id, current_user.id, ["owner", "manager"])

    team_repo = TeamRepository(db)
    existing = await team_repo.get_member(team_id, user_id)
    if not existing:
        raise NotFoundException(detail="Team member not found")

    # 마지막 소유자 제거 방지
    if existing.role == TeamRole.owner:
        members = await team_repo.get_team_members(team_id)
        owner_count = sum(1 for m in members if m.role == TeamRole.owner)
        if owner_count <= 1:
            raise BadRequestException(detail="Cannot remove the last owner of the team")

    removed = await team_repo.remove_member(team_id, user_id)
    if not removed:
        raise NotFoundException(detail="Team member not found")
