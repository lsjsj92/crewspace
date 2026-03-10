from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.database import get_db
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.label import LabelCreateRequest, LabelResponse, LabelUpdateRequest
from app.services import label_service

router = APIRouter()


@router.get("/projects/{project_id}/labels", response_model=list[LabelResponse])
async def list_labels(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[LabelResponse]:
    """Get all labels for a project."""
    return await label_service.get_project_labels(db, project_id)


@router.post("/projects/{project_id}/labels", response_model=LabelResponse, status_code=201)
async def create_label(
    project_id: UUID,
    data: LabelCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> LabelResponse:
    """Create a new label in the project."""
    return await label_service.create_label(db, project_id, data)


@router.patch("/labels/{label_id}", response_model=LabelResponse)
async def update_label(
    label_id: UUID,
    data: LabelUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> LabelResponse:
    """Update a label."""
    return await label_service.update_label(db, label_id, data)


@router.delete("/labels/{label_id}", response_model=MessageResponse)
async def delete_label(
    label_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> MessageResponse:
    """Delete a label."""
    await label_service.delete_label(db, label_id)
    return MessageResponse(message="Label deleted successfully")
