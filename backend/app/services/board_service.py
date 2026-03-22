from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_app_config
from app.exceptions.base import BadRequestException, NotFoundException
from app.models.board_column import BoardColumn
from app.models.card import Card
from app.models.user import User
from app.schemas.board import (
    ColumnCreateRequest,
    ColumnReorderRequest,
    ColumnResponse,
    ColumnUpdateRequest,
    ColumnWithCardsResponse,
)
from app.schemas.card import CardAssigneeResponse, CardResponse
from app.services.project_permission_service import check_project_permission


def _card_to_response(card: Card, prefix: str) -> CardResponse:
    """Card 모델을 CardResponse로 변환하고 프로젝트 prefix와 assignees를 설정한다."""
    resp = CardResponse.model_validate(card)
    resp.prefix = prefix
    resp.assignees = [CardAssigneeResponse.model_validate(a) for a in (card.assignees or [])]
    return resp


def _column_to_response(column: BoardColumn) -> ColumnResponse:
    return ColumnResponse.model_validate(column)


async def _get_project_columns(db: AsyncSession, project_id: UUID) -> list[BoardColumn]:
    """Fetch all non-deleted columns for a project, ordered by position."""
    result = await db.execute(
        select(BoardColumn)
        .where(
            BoardColumn.project_id == project_id,
            BoardColumn.deleted_at.is_(None),
        )
        .order_by(BoardColumn.position)
    )
    return list(result.scalars().all())


async def _get_column(db: AsyncSession, project_id: UUID, column_id: UUID) -> BoardColumn:
    """Fetch a single column belonging to a project, or raise NotFoundException."""
    result = await db.execute(
        select(BoardColumn).where(
            BoardColumn.id == column_id,
            BoardColumn.project_id == project_id,
            BoardColumn.deleted_at.is_(None),
        )
    )
    column = result.scalar_one_or_none()
    if not column:
        raise NotFoundException(detail="Column not found")
    return column


async def get_board(db: AsyncSession, project_id: UUID, current_user: User | None = None) -> list[ColumnWithCardsResponse]:
    """Get all columns for a project with their cards."""
    if current_user:
        await check_project_permission(db, project_id, current_user, ["manager", "member", "viewer"])
    columns = await _get_project_columns(db, project_id)

    # Get the project prefix for display_number
    from app.models.project import Project
    proj_result = await db.execute(select(Project).where(Project.id == project_id))
    project = proj_result.scalar_one_or_none()
    prefix = project.prefix if project else ""

    result: list[ColumnWithCardsResponse] = []
    for col in columns:
        # Get non-archived cards for this column, sorted by position
        # assignees를 함께 로드하여 N+1 쿼리를 방지한다
        cards_result = await db.execute(
            select(Card)
            .where(
                Card.column_id == col.id,
                Card.archived_at.is_(None),
                Card.deleted_at.is_(None),
            )
            .options(selectinload(Card.assignees))
            .order_by(Card.position)
        )
        cards = list(cards_result.scalars().all())

        col_resp = ColumnWithCardsResponse(
            id=col.id,
            project_id=col.project_id,
            name=col.name,
            position=col.position,
            is_end=col.is_end,
            wip_limit=col.wip_limit,
            cards=[_card_to_response(c, prefix) for c in cards],
        )
        result.append(col_resp)

    return result


async def create_column(
    db: AsyncSession,
    project_id: UUID,
    data: ColumnCreateRequest,
    current_user: User,
) -> ColumnResponse:
    """Create a new column. Inserts before the end column."""
    await check_project_permission(db, project_id, current_user, ["manager"])
    app_config = get_app_config()
    columns = await _get_project_columns(db, project_id)

    if len(columns) >= app_config.max_columns:
        raise BadRequestException(
            detail=f"Maximum of {app_config.max_columns} columns allowed"
        )

    # Find the end column and insert before it
    end_column = next((c for c in columns if c.is_end), None)

    if end_column:
        # New column goes right before end column
        new_position = end_column.position
        # Shift end column forward
        await db.execute(
            update(BoardColumn)
            .where(
                BoardColumn.project_id == project_id,
                BoardColumn.position >= new_position,
                BoardColumn.deleted_at.is_(None),
            )
            .values(position=BoardColumn.position + 1)
        )
    else:
        # No end column — append at end
        new_position = (columns[-1].position + 1) if columns else 0

    new_column = BoardColumn(
        project_id=project_id,
        name=data.name,
        position=new_position,
        is_end=False,
    )
    db.add(new_column)
    await db.flush()
    await db.refresh(new_column)

    return _column_to_response(new_column)


async def update_column(
    db: AsyncSession,
    project_id: UUID,
    column_id: UUID,
    data: ColumnUpdateRequest,
    current_user: User | None = None,
) -> ColumnResponse:
    """Update a column's properties."""
    if current_user:
        await check_project_permission(db, project_id, current_user, ["manager"])
    column = await _get_column(db, project_id, column_id)

    # If trying to unset is_end, ensure there is at least one other end column
    if data.is_end is False and column.is_end:
        columns = await _get_project_columns(db, project_id)
        end_columns = [c for c in columns if c.is_end and c.id != column_id]
        if not end_columns:
            raise BadRequestException(
                detail="Cannot remove end status from the only end column"
            )

    update_data = data.model_dump(exclude_unset=True)
    if update_data:
        for key, value in update_data.items():
            setattr(column, key, value)
        await db.flush()
        await db.refresh(column)

    return _column_to_response(column)


async def delete_column(
    db: AsyncSession,
    project_id: UUID,
    column_id: UUID,
    current_user: User | None = None,
) -> None:
    """Delete a column. Moves its cards to the previous column first."""
    if current_user:
        await check_project_permission(db, project_id, current_user, ["manager"])
    column = await _get_column(db, project_id, column_id)

    if column.is_end:
        raise BadRequestException(detail="Cannot delete the end column")

    columns = await _get_project_columns(db, project_id)

    app_config = get_app_config()
    if len(columns) <= app_config.min_columns:
        raise BadRequestException(
            detail=f"Minimum of {app_config.min_columns} columns required"
        )

    # Find the previous column to move cards to
    sorted_cols = sorted(columns, key=lambda c: c.position)
    col_index = next(i for i, c in enumerate(sorted_cols) if c.id == column_id)

    # Move cards to the previous column, or the next one if this is the first
    target_column = sorted_cols[col_index - 1] if col_index > 0 else sorted_cols[col_index + 1]

    # Move all cards from this column to the target
    await db.execute(
        update(Card)
        .where(Card.column_id == column_id, Card.deleted_at.is_(None))
        .values(column_id=target_column.id)
    )

    # Soft-delete the column
    from app.utils.datetime_utils import now_kst
    column.deleted_at = now_kst()
    await db.flush()

    # Rebalance positions for remaining columns
    remaining = [c for c in sorted_cols if c.id != column_id]
    for idx, col in enumerate(remaining):
        if col.position != idx:
            col.position = idx
    await db.flush()


async def reorder_columns(
    db: AsyncSession,
    project_id: UUID,
    data: ColumnReorderRequest,
    current_user: User | None = None,
) -> list[ColumnResponse]:
    """Reorder columns. End column must remain last."""
    if current_user:
        await check_project_permission(db, project_id, current_user, ["manager"])
    columns = await _get_project_columns(db, project_id)
    column_map = {c.id: c for c in columns}

    # Validate all column_ids belong to this project
    if set(data.column_ids) != set(column_map.keys()):
        raise BadRequestException(
            detail="Column IDs must match exactly the columns in this project"
        )

    # Validate end column is last
    last_col_id = data.column_ids[-1]
    last_col = column_map.get(last_col_id)
    if last_col and not last_col.is_end:
        # Check if any end column exists and isn't last
        for col_id in data.column_ids[:-1]:
            col = column_map.get(col_id)
            if col and col.is_end:
                raise BadRequestException(detail="End column must be last")

    # Update positions
    for idx, col_id in enumerate(data.column_ids):
        col = column_map[col_id]
        if col.position != idx:
            col.position = idx
    await db.flush()

    # Return updated columns in new order
    result: list[ColumnResponse] = []
    for col_id in data.column_ids:
        col = column_map[col_id]
        await db.refresh(col)
        result.append(_column_to_response(col))

    return result
