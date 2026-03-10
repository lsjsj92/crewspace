from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.database import get_db
from app.models.user import User
from app.schemas.board import (
    ColumnCreateRequest,
    ColumnReorderRequest,
    ColumnResponse,
    ColumnUpdateRequest,
    ColumnWithCardsResponse,
)
from app.schemas.common import MessageResponse
from app.services import board_service

router = APIRouter()


@router.get("/projects/{project_id}/columns", response_model=list[ColumnWithCardsResponse])
async def get_board(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[ColumnWithCardsResponse]:
    """Get the board with all columns and their cards."""
    return await board_service.get_board(db, project_id, current_user)


@router.post("/projects/{project_id}/columns", response_model=ColumnResponse, status_code=201)
async def create_column(
    project_id: UUID,
    data: ColumnCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ColumnResponse:
    """Create a new column in the project board."""
    return await board_service.create_column(db, project_id, data, current_user)


@router.patch("/projects/{project_id}/columns/{column_id}", response_model=ColumnResponse)
async def update_column(
    project_id: UUID,
    column_id: UUID,
    data: ColumnUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ColumnResponse:
    """Update a column's properties."""
    return await board_service.update_column(db, project_id, column_id, data, current_user)


@router.delete("/projects/{project_id}/columns/{column_id}", response_model=MessageResponse)
async def delete_column(
    project_id: UUID,
    column_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> MessageResponse:
    """Delete a column and move its cards to the previous column."""
    await board_service.delete_column(db, project_id, column_id, current_user)
    return MessageResponse(message="Column deleted successfully")


@router.post("/projects/{project_id}/columns/reorder", response_model=list[ColumnResponse])
async def reorder_columns(
    project_id: UUID,
    data: ColumnReorderRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[ColumnResponse]:
    """Reorder columns in the project board."""
    return await board_service.reorder_columns(db, project_id, data, current_user)
