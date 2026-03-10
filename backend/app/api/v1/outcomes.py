from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.database import get_db
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.outcome import OutcomeCreateRequest, OutcomeResponse, OutcomeUpdateRequest
from app.services import outcome_service

router = APIRouter()


@router.get("/projects/{project_id}/outcomes", response_model=list[OutcomeResponse])
async def list_project_outcomes(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[OutcomeResponse]:
    """List all outcomes for a project."""
    return await outcome_service.get_project_outcomes(db, project_id)


@router.post("/projects/{project_id}/outcomes", response_model=OutcomeResponse, status_code=201)
async def create_outcome(
    project_id: UUID,
    data: OutcomeCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> OutcomeResponse:
    """Create a new outcome for a project."""
    return await outcome_service.create_outcome(db, project_id, data, current_user)


@router.patch("/outcomes/{outcome_id}", response_model=OutcomeResponse)
async def update_outcome(
    outcome_id: UUID,
    data: OutcomeUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> OutcomeResponse:
    """Update an existing outcome."""
    return await outcome_service.update_outcome(db, outcome_id, data, current_user)


@router.delete("/outcomes/{outcome_id}", response_model=MessageResponse)
async def delete_outcome(
    outcome_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> MessageResponse:
    """Delete an outcome."""
    await outcome_service.delete_outcome(db, outcome_id, current_user)
    return MessageResponse(message="Outcome deleted successfully")
