from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project, ProjectStatus
from app.repositories.base_repository import BaseRepository


class ProjectRepository(BaseRepository[Project]):
    """Repository for Project-specific database operations."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Project, session)

    async def get_team_projects(
        self, team_id: UUID, status_filter: str | None = None
    ) -> list[Project]:
        """Fetch projects for a team. Excludes 'completed' by default unless a filter is specified."""
        stmt = select(Project).where(
            Project.team_id == team_id,
            Project.deleted_at.is_(None),
        )
        if status_filter:
            stmt = stmt.where(Project.status == ProjectStatus(status_filter))
        else:
            stmt = stmt.where(Project.status != ProjectStatus.completed)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_prefix(self, prefix: str) -> Project | None:
        """Fetch a project by its globally unique prefix."""
        result = await self.session.execute(
            select(Project).where(
                Project.prefix == prefix,
                Project.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def get_all_projects(
        self, status_filter: str | None = None
    ) -> list[Project]:
        """Fetch all projects (superadmin use)."""
        stmt = select(Project).where(Project.deleted_at.is_(None))
        if status_filter:
            stmt = stmt.where(Project.status == ProjectStatus(status_filter))
        stmt = stmt.order_by(Project.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
