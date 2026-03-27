# backend/app/services/project_service.py
# 프로젝트 관련 비즈니스 로직 (프로젝트 CRUD, 보드 칼럼 생성, 삭제 시 관련 데이터 정리)
from uuid import UUID

from sqlalchemy import delete as sa_delete, update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.base import (
    BadRequestException,
    ConflictException,
    ForbiddenException,
    NotFoundException,
)
from app.models.board_column import BoardColumn
from app.models.card import Card
from app.models.label import Label
from app.models.project import Project, ProjectMember, ProjectRole, ProjectStatus
from app.models.project_outcome import ProjectOutcome
from app.models.user import User
from app.repositories.board_column_repository import BoardColumnRepository
from app.repositories.project_member_repository import ProjectMemberRepository
from app.repositories.project_repository import ProjectRepository
from app.schemas.project import (
    BoardColumnResponse,
    ProjectCreateRequest,
    ProjectDetailResponse,
    ProjectResponse,
    ProjectUpdateRequest,
)
from app.services.project_permission_service import check_project_permission
from app.utils.datetime_utils import now_kst


def _project_response(project: Project) -> ProjectResponse:
    """Convert a Project model to ProjectResponse."""
    return ProjectResponse(
        id=project.id,
        team_id=project.team_id,
        name=project.name,
        description=project.description,
        prefix=project.prefix,
        status=project.status.value,
        start_date=project.start_date,
        end_date=project.end_date,
        created_at=project.created_at,
    )


async def create_project(
    db: AsyncSession,
    data: ProjectCreateRequest,
    current_user: User,
) -> ProjectResponse:
    """Create a new project. Superadmin only. Optionally assigns a manager."""
    if not current_user.is_superadmin:
        raise ForbiddenException(detail="Only superadmin can create projects")

    # prefix 중복 검사 (활성 프로젝트만 — partial unique index가 soft-deleted 행을 제외)
    project_repo = ProjectRepository(db)
    existing = await project_repo.get_by_prefix(data.prefix)
    if existing:
        raise ConflictException(detail=f"Project prefix '{data.prefix}' already exists")

    # 프로젝트 생성
    project = await project_repo.create(
        name=data.name,
        description=data.description,
        prefix=data.prefix,
        start_date=data.start_date,
        end_date=data.end_date,
        created_by=current_user.id,
    )

    # Create default board columns
    column_repo = BoardColumnRepository(db)
    await column_repo.create_default_columns(project.id)

    # Add manager if specified
    member_repo = ProjectMemberRepository(db)
    if data.manager_user_id:
        await member_repo.add_member(project.id, data.manager_user_id, ProjectRole.manager)
    else:
        # Add creator as manager
        await member_repo.add_member(project.id, current_user.id, ProjectRole.manager)

    return _project_response(project)


async def get_user_projects(
    db: AsyncSession,
    current_user: User,
    status: str | None = None,
) -> list[ProjectResponse]:
    """Get projects accessible to the current user."""
    if current_user.is_superadmin:
        project_repo = ProjectRepository(db)
        projects = await project_repo.get_all_projects(status_filter=status)
    else:
        member_repo = ProjectMemberRepository(db)
        projects = await member_repo.get_user_projects(current_user.id, status_filter=status)
    return [_project_response(p) for p in projects]


async def get_recent_projects(
    db: AsyncSession,
    current_user: User,
    limit: int = 5,
) -> list[ProjectResponse]:
    """Get recent projects for the sidebar."""
    if current_user.is_superadmin:
        project_repo = ProjectRepository(db)
        projects = await project_repo.get_all_projects(status_filter="active")
        projects = projects[:limit]
    else:
        member_repo = ProjectMemberRepository(db)
        projects = await member_repo.get_recent_projects(current_user.id, limit=limit)
    return [_project_response(p) for p in projects]


async def get_project(
    db: AsyncSession,
    project_id: UUID,
    current_user: User,
) -> ProjectDetailResponse:
    """Get project detail with board columns. Requires membership."""
    project_repo = ProjectRepository(db)
    project = await project_repo.get_by_id(project_id)
    if not project or project.deleted_at is not None:
        raise NotFoundException(detail="Project not found")

    await check_project_permission(db, project_id, current_user, ["manager", "member", "viewer"])

    column_repo = BoardColumnRepository(db)
    columns = await column_repo.get_project_columns(project_id)

    return ProjectDetailResponse(
        id=project.id,
        team_id=project.team_id,
        name=project.name,
        description=project.description,
        prefix=project.prefix,
        status=project.status.value,
        start_date=project.start_date,
        end_date=project.end_date,
        created_at=project.created_at,
        columns=[BoardColumnResponse.model_validate(c) for c in columns],
    )


async def update_project(
    db: AsyncSession,
    project_id: UUID,
    data: ProjectUpdateRequest,
    current_user: User,
) -> ProjectResponse:
    """프로젝트를 수정한다. manager 역할이 필요하다."""
    project_repo = ProjectRepository(db)
    project = await project_repo.get_by_id(project_id)
    if not project or project.deleted_at is not None:
        raise NotFoundException(detail="Project not found")

    await check_project_permission(db, project_id, current_user, ["manager"])

    update_data = data.model_dump(exclude_unset=True)
    if update_data:
        project = await project_repo.update(project_id, **update_data)
    return _project_response(project)


async def delete_project(
    db: AsyncSession,
    project_id: UUID,
    current_user: User,
) -> None:
    """프로젝트를 소프트 삭제하고 관련 데이터를 정리한다.

    partial unique index(WHERE deleted_at IS NULL)에 의해
    soft-delete된 프로젝트의 prefix는 unique 검사에서 자동 제외된다.
    관련 board_columns, cards, labels는 소프트 삭제하고,
    project_members, project_outcomes는 하드 삭제한다.
    superadmin only.
    """
    if not current_user.is_superadmin:
        raise ForbiddenException(detail="Only superadmin can delete projects")

    project_repo = ProjectRepository(db)
    project = await project_repo.get_by_id(project_id)
    if not project or project.deleted_at is not None:
        raise NotFoundException(detail="Project not found")

    now = now_kst()

    # partial unique index(WHERE deleted_at IS NULL)에 의해
    # soft-delete된 프로젝트의 prefix는 unique 검사에서 자동 제외되므로
    # prefix 변경 없이 삭제 가능

    # 관련 보드 칼럼 소프트 삭제
    await db.execute(
        sa_update(BoardColumn)
        .where(BoardColumn.project_id == project_id, BoardColumn.deleted_at.is_(None))
        .values(deleted_at=now)
    )

    # 관련 카드 소프트 삭제
    await db.execute(
        sa_update(Card)
        .where(Card.project_id == project_id, Card.deleted_at.is_(None))
        .values(deleted_at=now)
    )

    # 관련 레이블 소프트 삭제
    await db.execute(
        sa_update(Label)
        .where(Label.project_id == project_id, Label.deleted_at.is_(None))
        .values(deleted_at=now)
    )

    # 프로젝트 멤버 삭제 (SoftDeleteMixin 없음)
    await db.execute(
        sa_delete(ProjectMember).where(ProjectMember.project_id == project_id)
    )

    # 프로젝트 성과 삭제 (SoftDeleteMixin 없음)
    await db.execute(
        sa_delete(ProjectOutcome).where(ProjectOutcome.project_id == project_id)
    )

    # 프로젝트 소프트 삭제 (prefix 유지 — partial unique index가 자동 제외)
    await db.execute(
        sa_update(Project)
        .where(Project.id == project_id)
        .values(deleted_at=now)
    )
    await db.flush()


async def complete_project(
    db: AsyncSession,
    project_id: UUID,
    current_user: User,
) -> ProjectResponse:
    """프로젝트 상태를 '완료'로 변경한다. manager 역할이 필요하다."""
    project_repo = ProjectRepository(db)
    project = await project_repo.get_by_id(project_id)
    if not project or project.deleted_at is not None:
        raise NotFoundException(detail="Project not found")

    await check_project_permission(db, project_id, current_user, ["manager"])

    if project.status == ProjectStatus.completed:
        raise BadRequestException(detail="Project is already completed")

    project = await project_repo.update(project_id, status=ProjectStatus.completed)
    return _project_response(project)


# Legacy compatibility: keep get_team_projects for backward compatibility
async def get_team_projects(
    db: AsyncSession,
    team_id: UUID,
    current_user: User,
    status: str | None = None,
) -> list[ProjectResponse]:
    """Get all projects for a team. Legacy endpoint."""
    project_repo = ProjectRepository(db)
    projects = await project_repo.get_team_projects(team_id, status_filter=status)
    return [_project_response(p) for p in projects]
