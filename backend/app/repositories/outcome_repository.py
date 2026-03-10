from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project_outcome import ProjectOutcome
from app.repositories.base_repository import BaseRepository


class OutcomeRepository(BaseRepository[ProjectOutcome]):
    """Repository for ProjectOutcome CRUD operations."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(ProjectOutcome, session)

    async def get_project_outcomes(self, project_id: UUID) -> list[ProjectOutcome]:
        """Get all outcomes for a project, ordered by creation date descending."""
        result = await self.session.execute(
            select(ProjectOutcome)
            .where(ProjectOutcome.project_id == project_id)
            .order_by(ProjectOutcome.created_at.desc())
        )
        return list(result.scalars().all())
