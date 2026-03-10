from uuid import UUID

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_app_config
from app.exceptions.base import BadRequestException, ForbiddenException, NotFoundException
from app.models.board_column import BoardColumn
from app.models.card import Card, CardAssignee, CardPriority, CardType
from app.models.label import CardLabel, Label
from app.models.project import Project
from app.models.user import User
from app.repositories.card_repository import CardRepository
from app.schemas.card import (
    CardAssigneeRequest,
    CardAssigneeResponse,
    CardCreateRequest,
    CardDetailResponse,
    CardMoveRequest,
    CardResponse,
    CardUpdateRequest,
)
from app.schemas.comment import CommentResponse
from app.schemas.label import LabelResponse
from app.services.project_permission_service import check_project_permission
from app.utils.datetime_utils import now_kst


# --- Hierarchy rules: epic -> story -> task ---
_HIERARCHY = {
    "epic": None,          # epic can have no parent
    "story": "epic",       # story must be under epic
    "task": "story",       # task must be under story (or epic)
}

_ALLOWED_PARENTS = {
    "epic": set(),
    "story": {"epic"},
    "task": {"epic", "story"},
}


def _card_to_response(card: Card, prefix: str) -> CardResponse:
    resp = CardResponse.model_validate(card)
    resp.prefix = prefix
    return resp


def _card_to_detail_response(card: Card, prefix: str) -> CardDetailResponse:
    assignees = [
        CardAssigneeResponse.model_validate(a) for a in (card.assignees or [])
    ]
    labels = [
        LabelResponse.model_validate(cl.label) for cl in (card.labels or []) if cl.label
    ]
    children = [
        _card_to_response(c, prefix) for c in (card.children or [])
        if c.deleted_at is None
    ]
    comments = [
        CommentResponse.model_validate(c) for c in (card.comments or [])
        if c.deleted_at is None
    ]

    resp = CardDetailResponse(
        id=card.id,
        project_id=card.project_id,
        column_id=card.column_id,
        parent_id=card.parent_id,
        card_type=card.card_type.value if isinstance(card.card_type, CardType) else card.card_type,
        card_number=card.card_number,
        title=card.title,
        description=card.description,
        priority=card.priority.value if isinstance(card.priority, CardPriority) else card.priority,
        position=card.position,
        start_date=card.start_date,
        due_date=card.due_date,
        completed_at=card.completed_at,
        archived_at=card.archived_at,
        created_by=card.created_by,
        created_at=card.created_at,
        prefix=prefix,
        assignees=assignees,
        labels=labels,
        children=children,
        comments=comments,
    )
    return resp


async def _get_project_prefix(db: AsyncSession, project_id: UUID) -> str:
    result = await db.execute(select(Project.prefix).where(Project.id == project_id))
    prefix = result.scalar_one_or_none()
    return prefix or ""


async def _get_first_column(db: AsyncSession, project_id: UUID) -> BoardColumn:
    result = await db.execute(
        select(BoardColumn)
        .where(
            BoardColumn.project_id == project_id,
            BoardColumn.deleted_at.is_(None),
        )
        .order_by(BoardColumn.position)
        .limit(1)
    )
    col = result.scalar_one_or_none()
    if not col:
        raise BadRequestException(detail="Project has no columns")
    return col


async def _get_max_position_in_column(db: AsyncSession, column_id: UUID) -> int:
    from sqlalchemy import func as sqlfunc
    result = await db.execute(
        select(sqlfunc.coalesce(sqlfunc.max(Card.position), 0)).where(
            Card.column_id == column_id,
            Card.deleted_at.is_(None),
        )
    )
    return result.scalar_one()


async def _get_card_or_404(db: AsyncSession, card_id: UUID) -> Card:
    result = await db.execute(
        select(Card).where(Card.id == card_id, Card.deleted_at.is_(None))
    )
    card = result.scalar_one_or_none()
    if not card:
        raise NotFoundException(detail="Card not found")
    return card


async def create_card(
    db: AsyncSession,
    project_id: UUID,
    data: CardCreateRequest,
    current_user: User,
) -> CardResponse:
    """Create a new card in the project."""
    await check_project_permission(db, project_id, current_user, ["manager", "member"])
    app_config = get_app_config()
    card_repo = CardRepository(db)

    # Validate parent hierarchy
    if data.parent_id:
        parent = await _get_card_or_404(db, data.parent_id)
        parent_type = parent.card_type.value if isinstance(parent.card_type, CardType) else parent.card_type
        allowed = _ALLOWED_PARENTS.get(data.card_type, set())
        if parent_type not in allowed:
            raise BadRequestException(
                detail=f"A {data.card_type} cannot be a child of a {parent_type}"
            )

    # Determine column
    if data.column_id:
        col_result = await db.execute(
            select(BoardColumn).where(
                BoardColumn.id == data.column_id,
                BoardColumn.project_id == project_id,
                BoardColumn.deleted_at.is_(None),
            )
        )
        column = col_result.scalar_one_or_none()
        if not column:
            raise NotFoundException(detail="Column not found")
    else:
        column = await _get_first_column(db, project_id)

    # Next card number
    card_number = await card_repo.get_next_card_number(project_id)

    # Position: append at end
    max_pos = await _get_max_position_in_column(db, column.id)
    position = max_pos + app_config.position_gap

    card = await card_repo.create(
        project_id=project_id,
        column_id=column.id,
        parent_id=data.parent_id,
        card_type=CardType(data.card_type),
        card_number=card_number,
        title=data.title,
        description=data.description,
        priority=CardPriority(data.priority),
        position=position,
        start_date=data.start_date,
        due_date=data.due_date,
        created_by=current_user.id,
    )

    prefix = await _get_project_prefix(db, project_id)
    return _card_to_response(card, prefix)


async def update_card(
    db: AsyncSession,
    card_id: UUID,
    data: CardUpdateRequest,
    current_user: User,
) -> CardResponse:
    """Update card fields."""
    card = await _get_card_or_404(db, card_id)
    await check_project_permission(db, card.project_id, current_user, ["manager", "member"])

    update_data = data.model_dump(exclude_unset=True)
    if "priority" in update_data and update_data["priority"] is not None:
        update_data["priority"] = CardPriority(update_data["priority"])

    for key, value in update_data.items():
        setattr(card, key, value)

    await db.flush()
    await db.refresh(card)

    prefix = await _get_project_prefix(db, card.project_id)
    return _card_to_response(card, prefix)


async def delete_card(
    db: AsyncSession,
    card_id: UUID,
    current_user: User,
) -> None:
    """Soft-delete a card."""
    card = await _get_card_or_404(db, card_id)
    await check_project_permission(db, card.project_id, current_user, ["manager", "member"])
    card.deleted_at = now_kst()
    await db.flush()


async def move_card(
    db: AsyncSession,
    card_id: UUID,
    data: CardMoveRequest,
    current_user: User,
) -> CardResponse:
    """Move a card to a different column and/or position."""
    app_config = get_app_config()
    card = await _get_card_or_404(db, card_id)
    await check_project_permission(db, card.project_id, current_user, ["manager", "member"])

    # Get old and new columns
    old_col_result = await db.execute(
        select(BoardColumn).where(BoardColumn.id == card.column_id)
    )
    old_column = old_col_result.scalar_one_or_none()

    new_col_result = await db.execute(
        select(BoardColumn).where(
            BoardColumn.id == data.column_id,
            BoardColumn.deleted_at.is_(None),
        )
    )
    new_column = new_col_result.scalar_one_or_none()
    if not new_column:
        raise NotFoundException(detail="Target column not found")

    # Handle completed_at based on end column
    old_is_end = old_column.is_end if old_column else False
    if new_column.is_end and not old_is_end:
        card.completed_at = now_kst()
    elif not new_column.is_end and old_is_end:
        card.completed_at = None

    # Get cards in the target column to calculate position
    cards_in_target = await db.execute(
        select(Card)
        .where(
            Card.column_id == data.column_id,
            Card.id != card_id,
            Card.deleted_at.is_(None),
            Card.archived_at.is_(None),
        )
        .order_by(Card.position)
    )
    target_cards = list(cards_in_target.scalars().all())

    # Calculate position
    target_position = data.position
    if not target_cards:
        # Empty column — use the gap
        new_position = app_config.position_gap
    elif target_position <= 0:
        # Insert at the beginning
        first_pos = target_cards[0].position
        new_position = first_pos // 2 if first_pos > 1 else first_pos - app_config.position_gap
    elif target_position >= len(target_cards):
        # Insert at the end
        last_pos = target_cards[-1].position
        new_position = last_pos + app_config.position_gap
    else:
        # Insert between two cards
        prev_pos = target_cards[target_position - 1].position
        next_pos = target_cards[target_position].position
        new_position = (prev_pos + next_pos) // 2

        # Rebalance if gap is too small
        if next_pos - prev_pos < 2:
            for idx, c in enumerate(target_cards):
                c.position = (idx + 1) * app_config.position_gap
            await db.flush()
            # Recalculate after rebalance
            if target_position < len(target_cards):
                prev_pos = target_cards[target_position - 1].position
                next_pos = target_cards[target_position].position
                new_position = (prev_pos + next_pos) // 2
            else:
                new_position = target_cards[-1].position + app_config.position_gap

    card.column_id = data.column_id
    card.position = new_position
    await db.flush()
    await db.refresh(card)

    prefix = await _get_project_prefix(db, card.project_id)
    return _card_to_response(card, prefix)


async def get_card_detail(
    db: AsyncSession,
    card_id: UUID,
    current_user: User,
) -> CardDetailResponse:
    """Get a card with full details."""
    card_repo = CardRepository(db)
    card = await card_repo.get_card_with_details(card_id)
    if not card or card.deleted_at is not None:
        raise NotFoundException(detail="Card not found")

    await check_project_permission(db, card.project_id, current_user, ["manager", "member", "viewer"])

    prefix = await _get_project_prefix(db, card.project_id)
    return _card_to_detail_response(card, prefix)


async def get_children(
    db: AsyncSession,
    card_id: UUID,
    current_user: User,
) -> list[CardResponse]:
    """Get child cards of a card."""
    card = await _get_card_or_404(db, card_id)
    await check_project_permission(db, card.project_id, current_user, ["manager", "member", "viewer"])
    card_repo = CardRepository(db)
    children = await card_repo.get_children(card_id)

    prefix = await _get_project_prefix(db, card.project_id)
    return [_card_to_response(c, prefix) for c in children]


async def add_assignee(
    db: AsyncSession,
    card_id: UUID,
    data: CardAssigneeRequest,
    current_user: User,
) -> CardAssigneeResponse:
    """Add an assignee to a card."""
    card = await _get_card_or_404(db, card_id)
    await check_project_permission(db, card.project_id, current_user, ["manager", "member"])

    # Check if already assigned
    existing = await db.execute(
        select(CardAssignee).where(
            CardAssignee.card_id == card_id,
            CardAssignee.user_id == data.user_id,
        )
    )
    if existing.scalar_one_or_none():
        raise BadRequestException(detail="User is already assigned to this card")

    assignee = CardAssignee(card_id=card_id, user_id=data.user_id)
    db.add(assignee)
    await db.flush()
    await db.refresh(assignee)

    return CardAssigneeResponse.model_validate(assignee)


async def remove_assignee(
    db: AsyncSession,
    card_id: UUID,
    user_id: UUID,
    current_user: User,
) -> None:
    """Remove an assignee from a card."""
    card = await _get_card_or_404(db, card_id)
    await check_project_permission(db, card.project_id, current_user, ["manager", "member"])
    result = await db.execute(
        select(CardAssignee).where(
            CardAssignee.card_id == card_id,
            CardAssignee.user_id == user_id,
        )
    )
    assignee = result.scalar_one_or_none()
    if not assignee:
        raise NotFoundException(detail="Assignee not found")

    await db.execute(
        delete(CardAssignee).where(
            CardAssignee.card_id == card_id,
            CardAssignee.user_id == user_id,
        )
    )
    await db.flush()


async def add_label(
    db: AsyncSession,
    card_id: UUID,
    label_id: UUID,
    current_user: User,
) -> None:
    """Add a label to a card."""
    card = await _get_card_or_404(db, card_id)
    await check_project_permission(db, card.project_id, current_user, ["manager", "member"])

    # Verify label exists and belongs to the same project
    label_result = await db.execute(
        select(Label).where(
            Label.id == label_id,
            Label.project_id == card.project_id,
            Label.deleted_at.is_(None),
        )
    )
    if not label_result.scalar_one_or_none():
        raise NotFoundException(detail="Label not found")

    # Check if already added
    existing = await db.execute(
        select(CardLabel).where(
            CardLabel.card_id == card_id,
            CardLabel.label_id == label_id,
        )
    )
    if existing.scalar_one_or_none():
        raise BadRequestException(detail="Label is already on this card")

    card_label = CardLabel(card_id=card_id, label_id=label_id)
    db.add(card_label)
    await db.flush()


async def remove_label(
    db: AsyncSession,
    card_id: UUID,
    label_id: UUID,
    current_user: User,
) -> None:
    """Remove a label from a card."""
    card = await _get_card_or_404(db, card_id)
    await check_project_permission(db, card.project_id, current_user, ["manager", "member"])
    result = await db.execute(
        select(CardLabel).where(
            CardLabel.card_id == card_id,
            CardLabel.label_id == label_id,
        )
    )
    if not result.scalar_one_or_none():
        raise NotFoundException(detail="Card label not found")

    await db.execute(
        delete(CardLabel).where(
            CardLabel.card_id == card_id,
            CardLabel.label_id == label_id,
        )
    )
    await db.flush()
