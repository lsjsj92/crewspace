from urllib.parse import quote
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.config import get_app_config
from app.database import get_db
from app.models.user import User
from app.schemas.card import (
    CardAssigneeRequest,
    CardAssigneeResponse,
    CardCreateRequest,
    CardDetailResponse,
    CardMoveRequest,
    CardReorderRequest,
    CardResponse,
    CardUpdateRequest,
    CardWithChildrenResponse,
)
from app.schemas.common import MessageResponse
from app.services import card_service, wbs_export_service

router = APIRouter()

XLSX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


@router.get("/card-types")
async def get_card_types() -> dict:
    """Return card type configuration for the frontend."""
    config = get_app_config()
    return {
        "types": config.card_types,
        "completed_visible_days": config.completed_visible_days,
        "deadline_warning_days": config.deadline_warning_days,
    }


@router.get("/projects/{project_id}/cards", response_model=list[CardResponse])
async def list_project_cards(
    project_id: UUID,
    type: str | None = Query(None, description="Filter by card type"),
    assignee: UUID | None = Query(None, description="Filter by assignee user ID"),
    priority: str | None = Query(None, description="Filter by priority"),
    include_archived: bool = Query(False, description="Include archived cards (timeline full view)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[CardResponse]:
    """List all cards in a project with optional filters."""
    return await card_service.list_cards(
        db,
        project_id,
        current_user,
        card_type=type,
        assignee_id=assignee,
        priority=priority,
        include_archived=include_archived,
    )


@router.get("/projects/{project_id}/cards/check-duplicate")
async def check_duplicate_title(
    project_id: UUID,
    title: str = Query(..., description="Card title to check"),
    card_type: str = Query(..., description="Card type"),
    exclude_card_id: UUID | None = Query(None, description="Card ID to exclude"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """Check if a card with the same title and type exists in the project."""
    return await card_service.find_duplicate_titles(
        db, project_id, title, card_type, exclude_card_id, current_user
    )


@router.get("/projects/{project_id}/wbs-export")
async def export_project_wbs(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Response:
    """프로젝트 카드를 Epic별 시트로 구성한 WBS Excel 파일로 다운로드한다."""
    content, filename = await wbs_export_service.export_project_wbs(db, project_id, current_user)
    encoded_filename = quote(filename)
    return Response(
        content=content,
        media_type=XLSX_MEDIA_TYPE,
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}",
        },
    )


@router.post("/projects/{project_id}/cards", response_model=CardResponse, status_code=201)
async def create_card(
    project_id: UUID,
    data: CardCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> CardResponse:
    """Create a new card in the project."""
    return await card_service.create_card(db, project_id, data, current_user)


@router.get("/cards/{card_id}", response_model=CardDetailResponse)
async def get_card(
    card_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> CardDetailResponse:
    """Get a card with full details."""
    return await card_service.get_card_detail(db, card_id, current_user)


@router.patch("/cards/{card_id}", response_model=CardResponse)
async def update_card(
    card_id: UUID,
    data: CardUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> CardResponse:
    """Update card fields."""
    return await card_service.update_card(db, card_id, data, current_user)


@router.delete("/cards/{card_id}", response_model=MessageResponse)
async def delete_card(
    card_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> MessageResponse:
    """Soft-delete a card."""
    await card_service.delete_card(db, card_id, current_user)
    return MessageResponse(message="Card deleted successfully")


@router.post("/cards/{card_id}/move", response_model=CardResponse)
async def move_card(
    card_id: UUID,
    data: CardMoveRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> CardResponse:
    """Move a card to a different column and/or position."""
    return await card_service.move_card(db, card_id, data, current_user)


@router.post("/cards/{card_id}/reorder", response_model=CardResponse)
async def reorder_card(
    card_id: UUID,
    data: CardReorderRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> CardResponse:
    """Reorder a card within its hierarchy."""
    return await card_service.reorder_in_hierarchy(db, card_id, data, current_user)


@router.get("/cards/{card_id}/children", response_model=list[CardWithChildrenResponse])
async def get_children(
    card_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[CardWithChildrenResponse]:
    """Get child cards of a card, each with its direct children."""
    return await card_service.get_children(db, card_id, current_user)


@router.post("/cards/{card_id}/assignees", response_model=CardAssigneeResponse, status_code=201)
async def add_assignee(
    card_id: UUID,
    data: CardAssigneeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> CardAssigneeResponse:
    """Add an assignee to a card."""
    return await card_service.add_assignee(db, card_id, data, current_user)


@router.delete("/cards/{card_id}/assignees/{user_id}", response_model=MessageResponse)
async def remove_assignee(
    card_id: UUID,
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> MessageResponse:
    """Remove an assignee from a card."""
    await card_service.remove_assignee(db, card_id, user_id, current_user)
    return MessageResponse(message="Assignee removed successfully")


@router.post("/cards/{card_id}/labels/{label_id}", response_model=MessageResponse, status_code=201)
async def add_label(
    card_id: UUID,
    label_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> MessageResponse:
    """Add a label to a card."""
    await card_service.add_label(db, card_id, label_id, current_user)
    return MessageResponse(message="Label added to card")


@router.delete("/cards/{card_id}/labels/{label_id}", response_model=MessageResponse)
async def remove_label(
    card_id: UUID,
    label_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> MessageResponse:
    """Remove a label from a card."""
    await card_service.remove_label(db, card_id, label_id, current_user)
    return MessageResponse(message="Label removed from card")
