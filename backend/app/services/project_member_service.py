from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.base import BadRequestException, NotFoundException
from app.models.project import ProjectRole
from app.models.user import User
from app.repositories.project_member_repository import ProjectMemberRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import UserResponse
from app.schemas.project import (
    AddProjectMemberRequest,
    ProjectMemberResponse,
    UpdateProjectMemberRoleRequest,
)
from app.services.project_permission_service import check_project_permission


def _member_response(member) -> ProjectMemberResponse:
    """ProjectMember를 ProjectMemberResponse로 변환한다."""
    user_resp = UserResponse.model_validate(member.user) if member.user else None
    return ProjectMemberResponse(
        id=member.id,
        project_id=member.project_id,
        user_id=member.user_id,
        role=member.role.value,
        joined_at=member.joined_at,
        user=user_resp,
    )


async def get_members(
    db: AsyncSession,
    project_id: UUID,
    current_user: User,
) -> list[ProjectMemberResponse]:
    """프로젝트 멤버 목록을 반환한다."""
    await check_project_permission(db, project_id, current_user, ["manager", "member", "viewer"])
    repo = ProjectMemberRepository(db)
    members = await repo.get_project_members(project_id)
    return [_member_response(m) for m in members]


async def add_member(
    db: AsyncSession,
    project_id: UUID,
    data: AddProjectMemberRequest,
    current_user: User,
) -> ProjectMemberResponse:
    """프로젝트에 멤버를 추가한다. manager 역할이 필요하다."""
    await check_project_permission(db, project_id, current_user, ["manager"])

    repo = ProjectMemberRepository(db)

    # Check user exists
    user_repo = UserRepository(db)
    target_user = await user_repo.get_by_id(data.user_id)
    if not target_user:
        raise NotFoundException(detail="User not found")

    # Check if already a member
    existing = await repo.get_member(project_id, data.user_id)
    if existing:
        raise BadRequestException(detail="User is already a member of this project")

    try:
        role = ProjectRole(data.role)
    except ValueError:
        raise BadRequestException(detail=f"Invalid role: {data.role}")

    member = await repo.add_member(project_id, data.user_id, role)
    # Refresh to get user relationship
    member = await repo.get_member(project_id, data.user_id)
    return _member_response(member)


async def update_member_role(
    db: AsyncSession,
    project_id: UUID,
    user_id: UUID,
    data: UpdateProjectMemberRoleRequest,
    current_user: User,
) -> ProjectMemberResponse:
    """프로젝트 멤버의 역할을 변경한다. manager 역할이 필요하다."""
    await check_project_permission(db, project_id, current_user, ["manager"])

    repo = ProjectMemberRepository(db)
    existing = await repo.get_member(project_id, user_id)
    if not existing:
        raise NotFoundException(detail="Project member not found")

    try:
        role = ProjectRole(data.role)
    except ValueError:
        raise BadRequestException(detail=f"Invalid role: {data.role}")

    member = await repo.update_member_role(project_id, user_id, role)
    return _member_response(member)


async def remove_member(
    db: AsyncSession,
    project_id: UUID,
    user_id: UUID,
    current_user: User,
) -> None:
    """프로젝트에서 멤버를 제거한다. manager 역할이 필요하다."""
    await check_project_permission(db, project_id, current_user, ["manager"])

    repo = ProjectMemberRepository(db)
    existing = await repo.get_member(project_id, user_id)
    if not existing:
        raise NotFoundException(detail="Project member not found")

    # Prevent removing last manager
    if existing.role == ProjectRole.manager:
        members = await repo.get_project_members(project_id)
        manager_count = sum(1 for m in members if m.role == ProjectRole.manager)
        if manager_count <= 1:
            raise BadRequestException(detail="Cannot remove the last manager of the project")

    removed = await repo.remove_member(project_id, user_id)
    if not removed:
        raise NotFoundException(detail="Project member not found")
