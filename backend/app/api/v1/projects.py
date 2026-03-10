from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, require_superadmin
from app.database import get_db
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.project import (
    AddProjectMemberRequest,
    ProjectCreateRequest,
    ProjectDetailResponse,
    ProjectMemberResponse,
    ProjectResponse,
    ProjectUpdateRequest,
    UpdateProjectMemberRoleRequest,
)
from app.services import project_service, project_member_service

router = APIRouter()


# --- Project CRUD ---

@router.post("/projects", response_model=ProjectResponse, status_code=201)
async def create_project(
    data: ProjectCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_superadmin),
) -> ProjectResponse:
    """Create a new project. Superadmin only."""
    return await project_service.create_project(db, data, current_user)


@router.get("/projects", response_model=list[ProjectResponse])
async def list_projects(
    status: str | None = Query(None, description="Filter by status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[ProjectResponse]:
    """List projects accessible to the current user."""
    return await project_service.get_user_projects(db, current_user, status=status)


@router.get("/projects/recent", response_model=list[ProjectResponse])
async def list_recent_projects(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[ProjectResponse]:
    """Get recent activity projects for sidebar."""
    return await project_service.get_recent_projects(db, current_user)


@router.get("/projects/{project_id}", response_model=ProjectDetailResponse)
async def get_project(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ProjectDetailResponse:
    """Get project details with board columns."""
    return await project_service.get_project(db, project_id, current_user)


@router.patch("/projects/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: UUID,
    data: ProjectUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ProjectResponse:
    """Update project information."""
    return await project_service.update_project(db, project_id, data, current_user)


@router.delete("/projects/{project_id}", response_model=MessageResponse)
async def delete_project(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_superadmin),
) -> MessageResponse:
    """Soft-delete a project. Superadmin only."""
    await project_service.delete_project(db, project_id, current_user)
    return MessageResponse(message="Project deleted successfully")


@router.patch("/projects/{project_id}/complete", response_model=ProjectResponse)
async def complete_project(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ProjectResponse:
    """Mark a project as completed."""
    return await project_service.complete_project(db, project_id, current_user)


# --- Project Members ---

@router.get("/projects/{project_id}/members", response_model=list[ProjectMemberResponse])
async def list_project_members(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[ProjectMemberResponse]:
    """List members of a project."""
    return await project_member_service.get_members(db, project_id, current_user)


@router.post("/projects/{project_id}/members", response_model=ProjectMemberResponse, status_code=201)
async def add_project_member(
    project_id: UUID,
    data: AddProjectMemberRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ProjectMemberResponse:
    """Add a member to a project. Manager role required."""
    return await project_member_service.add_member(db, project_id, data, current_user)


@router.patch("/projects/{project_id}/members/{user_id}", response_model=ProjectMemberResponse)
async def update_project_member_role(
    project_id: UUID,
    user_id: UUID,
    data: UpdateProjectMemberRoleRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ProjectMemberResponse:
    """Update a project member's role. Manager role required."""
    return await project_member_service.update_member_role(db, project_id, user_id, data, current_user)


@router.delete("/projects/{project_id}/members/{user_id}", response_model=MessageResponse)
async def remove_project_member(
    project_id: UUID,
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> MessageResponse:
    """Remove a member from a project. Manager role required."""
    await project_member_service.remove_member(db, project_id, user_id, current_user)
    return MessageResponse(message="Member removed successfully")


# --- Legacy: Team Projects (deprecated, kept for backward compatibility) ---

@router.get("/teams/{team_id}/projects", response_model=list[ProjectResponse])
async def list_team_projects(
    team_id: UUID,
    status: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[ProjectResponse]:
    """List projects for a team (deprecated, use GET /projects instead)."""
    return await project_service.get_team_projects(db, team_id, current_user, status=status)


@router.post("/teams/{team_id}/projects", response_model=ProjectResponse, status_code=201)
async def create_team_project(
    team_id: UUID,
    data: ProjectCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ProjectResponse:
    """Create a project in a team (deprecated, use POST /projects instead)."""
    return await project_service.create_project(db, data, current_user)
