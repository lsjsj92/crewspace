from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.config import get_app_config
from app.database import get_db
from app.models.user import User
from app.repositories.card_repository import CardRepository
from app.schemas.card import (
    CardAssigneeRequest,
    CardAssigneeResponse,
    CardCreateRequest,
    CardDetailResponse,
    CardMoveRequest,
    CardReorderRequest,
    CardResponse,
    CardUpdateRequest,
)
from app.schemas.common import MessageResponse
from app.services import card_service

router = APIRouter()


@router.get("/card-types")
async def get_card_types() -> dict:
    """Return card type configuration for the frontend."""
    config = get_app_config()
    return {
        "types": config.card_types,
        "completed_visible_days": config.completed_visible_days,
    }


@router.get("/projects/{project_id}/cards", response_model=list[CardResponse])
async def list_project_cards(
    project_id: UUID,
    type: str | None = Query(None, description="Filter by card type"),
    assignee: UUID | None = Query(None, description="Filter by assignee user ID"),
    priority: str | None = Query(None, description="Filter by priority"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[CardResponse]:
    """List all cards in a project with optional filters."""
    from app.services.project_permission_service import check_project_permission
    await check_project_permission(db, project_id, current_user, ["manager", "member", "viewer"])
    repo = CardRepository(db)
    cards = await repo.get_project_cards(
        project_id, card_type=type, assignee_id=assignee, priority=priority
    )
    from app.services.card_service import _get_project_prefix, _card_to_response
    prefix = await _get_project_prefix(db, project_id)
    return [_card_to_response(c, prefix) for c in cards]


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
    from app.services.project_permission_service import check_project_permission
    await check_project_permission(db, project_id, current_user, ["manager", "member", "viewer"])
    repo = CardRepository(db)
    duplicates = await repo.find_by_title(project_id, title, card_type, exclude_card_id)
    return {
        "has_duplicate": len(duplicates) > 0,
        "count": len(duplicates),
        "cards": [
            {"id": str(c.id), "card_number": c.card_number, "title": c.title}
            for c in duplicates
        ],
    }


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


@router.get("/cards/{card_id}/children", response_model=list[CardResponse])
async def get_children(
    card_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[CardResponse]:
    """Get child cards of a card."""
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
