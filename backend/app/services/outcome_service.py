from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.base import NotFoundException
from app.models.user import User
from app.repositories.outcome_repository import OutcomeRepository
from app.schemas.outcome import OutcomeCreateRequest, OutcomeResponse, OutcomeUpdateRequest


async def get_project_outcomes(
    db: AsyncSession,
    project_id: UUID,
) -> list[OutcomeResponse]:
    """Get all outcomes for a project."""
    repo = OutcomeRepository(db)
    outcomes = await repo.get_project_outcomes(project_id)
    return [OutcomeResponse.model_validate(o) for o in outcomes]


async def create_outcome(
    db: AsyncSession,
    project_id: UUID,
    data: OutcomeCreateRequest,
    current_user: User,
) -> OutcomeResponse:
    """Create a new outcome for a project."""
    repo = OutcomeRepository(db)
    outcome = await repo.create(
        project_id=project_id,
        title=data.title,
        description=data.description,
        achieved_at=data.achieved_at,
        created_by=current_user.id,
    )
    return OutcomeResponse.model_validate(outcome)


async def update_outcome(
    db: AsyncSession,
    outcome_id: UUID,
    data: OutcomeUpdateRequest,
    current_user: User,
) -> OutcomeResponse:
    """Update an existing outcome."""
    repo = OutcomeRepository(db)
    outcome = await repo.get_by_id(outcome_id)
    if not outcome:
        raise NotFoundException(detail="Outcome not found")

    update_data = data.model_dump(exclude_unset=True)
    updated = await repo.update(outcome_id, **update_data)
    if not updated:
        raise NotFoundException(detail="Outcome not found")

    return OutcomeResponse.model_validate(updated)


async def delete_outcome(
    db: AsyncSession,
    outcome_id: UUID,
    current_user: User,
) -> None:
    """Delete an outcome."""
    repo = OutcomeRepository(db)
    outcome = await repo.get_by_id(outcome_id)
    if not outcome:
        raise NotFoundException(detail="Outcome not found")

    await db.delete(outcome)
    await db.flush()
