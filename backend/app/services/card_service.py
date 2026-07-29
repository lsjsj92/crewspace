# backend/app/services/card_service.py
# 카드 비즈니스 로직 서비스

from datetime import date, timedelta
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import AppConfig, get_app_config
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
    CardReorderRequest,
    CardResponse,
    CardUpdateRequest,
    CardWithChildrenResponse,
    ParentCardInfo,
)
from app.schemas.comment import CommentResponse
from app.schemas.label import LabelResponse
from app.services.project_permission_service import check_project_permission
from app.utils.datetime_utils import add_months, now_kst, today_kst


def _build_parent_chain(card: Card) -> ParentCardInfo | None:
    """삭제되지 않은 상위 카드 체인을 ParentCardInfo로 변환한다 (Task -> Story -> Epic)."""
    parent = card.parent
    if parent is None or parent.deleted_at is not None:
        return None
    card_type = parent.card_type.value if isinstance(parent.card_type, CardType) else parent.card_type
    return ParentCardInfo(
        id=parent.id,
        card_type=card_type,
        card_number=parent.card_number,
        title=parent.title,
        parent=_build_parent_chain(parent),
    )


def card_to_response(card: Card, prefix: str) -> CardResponse:
    resp = CardResponse.model_validate(card)
    resp.prefix = prefix
    resp.column_name = card.column.name if card.column else ""
    resp.parent = _build_parent_chain(card)
    return resp


def _to_parent_info(card: Card) -> ParentCardInfo:
    """카드를 상위 카드 요약 정보로 변환한다 (체인 없이 단일 항목)."""
    card_type = card.card_type.value if isinstance(card.card_type, CardType) else card.card_type
    return ParentCardInfo(
        id=card.id,
        card_type=card_type,
        card_number=card.card_number,
        title=card.title,
    )


async def _validate_linked_parents(
    db: AsyncSession,
    card_id: UUID | None,
    project_id: UUID,
    card_type: str,
    primary_parent_id: UUID | None,
    linked_ids: list[UUID],
    app_config: AppConfig,
) -> list[UUID]:
    """보조 상위 연결 목록을 검증하고 중복이 제거된 ID 목록을 반환한다.

    규칙: 자기 자신/주 부모 제외, 주 부모 포함 총 부모 수는 max_parents 이하,
    같은 프로젝트의 허용된 부모 타입 카드만 연결 가능.
    """
    deduped: list[UUID] = []
    for pid in linked_ids:
        if pid == card_id:
            raise BadRequestException(detail="A card cannot be linked to itself")
        if pid != primary_parent_id and pid not in deduped:
            deduped.append(pid)

    total_parents = (1 if primary_parent_id else 0) + len(deduped)
    if total_parents > app_config.max_parents:
        raise BadRequestException(
            detail=f"A card can have at most {app_config.max_parents} parents"
        )

    allowed = app_config.allowed_parents.get(card_type, set())
    for pid in deduped:
        parent = await _get_card_or_404(db, pid)
        if parent.project_id != project_id:
            raise BadRequestException(detail="Linked parent must be in the same project")
        parent_type = parent.card_type.value if isinstance(parent.card_type, CardType) else parent.card_type
        if parent_type not in allowed:
            raise BadRequestException(
                detail=f"A {card_type} cannot be linked under a {parent_type}"
            )
    return deduped


async def _to_response_with_parents(db: AsyncSession, card: Card) -> CardResponse:
    """상위 카드 체인을 명시적으로 로딩한 뒤 응답으로 변환한다 (async lazy load 방지)."""
    card_repo = CardRepository(db)
    loaded = await card_repo.get_card_with_parents(card.id)
    prefix = await _get_project_prefix(db, card.project_id)
    return card_to_response(loaded or card, prefix)


def _default_due_date(start: date, card_type: str, app_config: AppConfig) -> date | None:
    """카드 타입별 기본 기간 설정으로 종료일을 계산한다. 설정이 없으면 None."""
    duration = app_config.default_durations.get(card_type)
    if not duration:
        return None
    unit = duration.get("unit")
    amount = int(duration.get("amount", 0))
    if amount <= 0:
        return None
    if unit == "month":
        return add_months(start, amount)
    if unit == "week":
        return start + timedelta(weeks=amount)
    if unit == "day":
        return start + timedelta(days=amount)
    return None


def _card_to_detail_response(
    card: Card, prefix: str, linked_parents: list[Card] | None = None
) -> CardDetailResponse:
    assignees = [
        CardAssigneeResponse.model_validate(a) for a in (card.assignees or [])
    ]
    labels = [
        LabelResponse.model_validate(cl.label) for cl in (card.labels or []) if cl.label
    ]
    children = [
        card_to_response(c, prefix) for c in (card.children or [])
        if c.deleted_at is None
    ]
    comments = [
        CommentResponse.model_validate(c) for c in (card.comments or [])
        if c.deleted_at is None
    ]

    # 삭제되지 않은 상위 카드 체인만 포함한다
    parent_info = _build_parent_chain(card)

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
        column_name=card.column.name if card.column else "",
        assignees=assignees,
        labels=labels,
        children=children,
        comments=comments,
        parent=parent_info,
        linked_parents=[_to_parent_info(p) for p in (linked_parents or [])],
    )
    return resp


async def _get_project_prefix(db: AsyncSession, project_id: UUID) -> str:
    result = await db.execute(select(Project.prefix).where(Project.id == project_id))
    prefix = result.scalar_one_or_none()
    return prefix or ""


async def list_cards(
    db: AsyncSession,
    project_id: UUID,
    current_user: User,
    card_type: str | None = None,
    assignee_id: UUID | None = None,
    priority: str | None = None,
    include_archived: bool = False,
) -> list[CardResponse]:
    """프로젝트 카드 목록을 조회한다."""
    await check_project_permission(db, project_id, current_user, ["manager", "member", "viewer"])
    card_repo = CardRepository(db)
    cards = await card_repo.get_project_cards(
        project_id,
        card_type=card_type,
        assignee_id=assignee_id,
        priority=priority,
        include_archived=include_archived,
    )
    prefix = await _get_project_prefix(db, project_id)
    return [card_to_response(c, prefix) for c in cards]


async def find_duplicate_titles(
    db: AsyncSession,
    project_id: UUID,
    title: str,
    card_type: str,
    exclude_card_id: UUID | None,
    current_user: User,
) -> dict:
    """같은 제목과 타입의 카드 존재 여부를 확인한다."""
    await check_project_permission(db, project_id, current_user, ["manager", "member", "viewer"])
    card_repo = CardRepository(db)
    duplicates = await card_repo.find_by_title(project_id, title, card_type, exclude_card_id)
    return {
        "has_duplicate": len(duplicates) > 0,
        "count": len(duplicates),
        "cards": [
            {"id": str(c.id), "card_number": c.card_number, "title": c.title}
            for c in duplicates
        ],
    }


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
    result = await db.execute(
        select(func.coalesce(func.max(Card.position), 0)).where(
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

    # Validate parent hierarchy using config
    allowed_parents = app_config.allowed_parents
    independent_types = app_config.independent_types

    if data.parent_id:
        parent = await _get_card_or_404(db, data.parent_id)
        parent_type = parent.card_type.value if isinstance(parent.card_type, CardType) else parent.card_type
        allowed = allowed_parents.get(data.card_type, set())
        if parent_type not in allowed:
            raise BadRequestException(
                detail=f"A {data.card_type} cannot be a child of a {parent_type}"
            )
    else:
        if data.card_type not in independent_types:
            raise BadRequestException(
                detail=f"A {data.card_type} card must have a parent"
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

    # 보조 상위 연결 검증 (카드 생성 전에 실패를 조기 확정)
    linked_parent_ids = await _validate_linked_parents(
        db, None, project_id, data.card_type, data.parent_id, data.linked_parent_ids, app_config
    )

    # 날짜 기본값: 시작일은 KST 오늘, 종료일은 타입별 기본 기간 적용
    start_date = data.start_date or today_kst()
    due_date = data.due_date or _default_due_date(start_date, data.card_type, app_config)

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
        start_date=start_date,
        due_date=due_date,
        created_by=current_user.id,
    )

    # 생성자를 기본 담당자로 자동 할당
    db.add(CardAssignee(card_id=card.id, user_id=current_user.id))
    await db.flush()
    await db.refresh(card, attribute_names=["assignees"])

    # 보조 상위 연결 저장
    if linked_parent_ids:
        await card_repo.replace_links(card.id, linked_parent_ids)

    return await _to_response_with_parents(db, card)


async def update_card(
    db: AsyncSession,
    card_id: UUID,
    data: CardUpdateRequest,
    current_user: User,
) -> CardResponse:
    """카드 필드 업데이트."""
    card = await _get_card_or_404(db, card_id)
    await check_project_permission(db, card.project_id, current_user, ["manager", "member"])

    update_data = data.model_dump(exclude_unset=True)
    # 보조 상위 연결은 setattr 대상이 아니므로 분리해서 별도 처리한다
    linked_parent_ids = update_data.pop("linked_parent_ids", None)

    # parent_id 변경 시 계층 구조 검증
    if "parent_id" in update_data:
        new_parent_id = update_data["parent_id"]
        app_config = get_app_config()
        card_type = card.card_type.value if isinstance(card.card_type, CardType) else card.card_type

        if new_parent_id is not None:
            # 자기 자신을 부모로 설정할 수 없음
            if new_parent_id == card_id:
                raise BadRequestException(detail="A card cannot be its own parent")

            parent = await _get_card_or_404(db, new_parent_id)
            parent_type = parent.card_type.value if isinstance(parent.card_type, CardType) else parent.card_type

            # 같은 프로젝트에 속해야 함
            if parent.project_id != card.project_id:
                raise BadRequestException(detail="Parent card must be in the same project")

            # 허용된 부모 타입 검증
            allowed = app_config.allowed_parents.get(card_type, set())
            if parent_type not in allowed:
                raise BadRequestException(
                    detail=f"A {card_type} cannot be a child of a {parent_type}"
                )

            # 순환 참조 방지
            card_repo = CardRepository(db)

            async def _is_descendant(ancestor_id: UUID, target_id: UUID) -> bool:
                children = await card_repo.get_children(ancestor_id)
                for child in children:
                    if child.id == target_id:
                        return True
                    if await _is_descendant(child.id, target_id):
                        return True
                return False

            if await _is_descendant(card_id, new_parent_id):
                raise BadRequestException(detail="Cannot create a circular hierarchy")
        else:
            # parent_id를 None으로 설정 시 독립 가능 여부 확인
            if card_type not in app_config.independent_types:
                raise BadRequestException(
                    detail=f"A {card_type} card must have a parent"
                )

    if "priority" in update_data and update_data["priority"] is not None:
        update_data["priority"] = CardPriority(update_data["priority"])

    for key, value in update_data.items():
        setattr(card, key, value)

    await db.flush()
    await db.refresh(card)

    card_repo = CardRepository(db)
    card_type = card.card_type.value if isinstance(card.card_type, CardType) else card.card_type

    # 주 부모로 승격된 카드가 보조 연결에 남아 있으면 제거한다
    if "parent_id" in update_data and card.parent_id is not None:
        await card_repo.remove_link(card_id, card.parent_id)

    # 보조 상위 연결 전체 교체
    if linked_parent_ids is not None:
        app_config = get_app_config()
        validated_ids = await _validate_linked_parents(
            db, card_id, card.project_id, card_type, card.parent_id, linked_parent_ids, app_config
        )
        await card_repo.replace_links(card_id, validated_ids)

    return await _to_response_with_parents(db, card)


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

    return await _to_response_with_parents(db, card)


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
    linked_parents = await card_repo.get_linked_parents(card_id)
    return _card_to_detail_response(card, prefix, linked_parents)


def _card_to_children_response(card: Card, prefix: str) -> CardWithChildrenResponse:
    """카드와 직계 자식(1단계)을 함께 응답으로 변환한다."""
    base = card_to_response(card, prefix)
    grandchildren = sorted(
        (c for c in (card.children or []) if c.deleted_at is None),
        key=lambda c: c.position,
    )
    return CardWithChildrenResponse(
        **base.model_dump(exclude={"display_number"}),
        children=[card_to_response(c, prefix) for c in grandchildren],
    )


async def _child_response_with_links(
    card_repo: CardRepository, card: Card, prefix: str, is_linked: bool
) -> CardWithChildrenResponse:
    """자식 카드 응답에 보조 연결된 손자 카드까지 병합한다."""
    resp = _card_to_children_response(card, prefix)
    resp.is_linked = is_linked
    existing_ids = {c.id for c in (card.children or [])}
    for grandchild in await card_repo.get_linked_children(card.id):
        if grandchild.id in existing_ids:
            continue
        grandchild_resp = card_to_response(grandchild, prefix)
        grandchild_resp.is_linked = True
        resp.children.append(grandchild_resp)
    return resp


async def get_children(
    db: AsyncSession,
    card_id: UUID,
    current_user: User,
) -> list[CardWithChildrenResponse]:
    """자식 카드 목록을 각 자식의 직계 자식과 함께 반환한다 (Epic -> Story -> Task 표시용).

    직계 자식 외에 보조 연결(card_links)로 이 카드에 묶인 카드도 함께 반환한다.
    """
    card = await _get_card_or_404(db, card_id)
    await check_project_permission(db, card.project_id, current_user, ["manager", "member", "viewer"])
    card_repo = CardRepository(db)
    children = await card_repo.get_children(card_id)
    linked_children = await card_repo.get_linked_children(card_id)

    prefix = await _get_project_prefix(db, card.project_id)
    responses = [
        await _child_response_with_links(card_repo, c, prefix, is_linked=False)
        for c in children
    ]
    direct_ids = {c.id for c in children}
    for c in linked_children:
        if c.id in direct_ids:
            continue
        responses.append(
            await _child_response_with_links(card_repo, c, prefix, is_linked=True)
        )
    return responses


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


async def reorder_in_hierarchy(
    db: AsyncSession,
    card_id: UUID,
    data: CardReorderRequest,
    current_user: User,
) -> CardResponse:
    """Timeline DnD 등에서 같은 parent 내 siblings 간 순서를 변경하거나 parent를 이동한다."""
    app_config = get_app_config()
    card = await _get_card_or_404(db, card_id)
    await check_project_permission(db, card.project_id, current_user, ["manager", "member"])

    card_repo = CardRepository(db)
    card_type = card.card_type.value if isinstance(card.card_type, CardType) else card.card_type

    # parent_id가 변경되는 경우 계층 구조 검증
    if data.parent_id != card.parent_id:
        if data.parent_id is not None:
            # 자기 자신을 부모로 설정할 수 없음
            if data.parent_id == card_id:
                raise BadRequestException(detail="A card cannot be its own parent")

            parent = await _get_card_or_404(db, data.parent_id)
            parent_type = parent.card_type.value if isinstance(parent.card_type, CardType) else parent.card_type

            # 같은 프로젝트에 속해야 함
            if parent.project_id != card.project_id:
                raise BadRequestException(detail="Parent card must be in the same project")

            # 허용된 부모 타입 검증
            allowed = app_config.allowed_parents.get(card_type, set())
            if parent_type not in allowed:
                raise BadRequestException(
                    detail=f"A {card_type} cannot be a child of a {parent_type}"
                )

            # 순환 참조 방지: 이동 대상이 현재 카드의 자손이면 안 됨
            async def _is_descendant(ancestor_id: UUID, target_id: UUID) -> bool:
                children = await card_repo.get_children(ancestor_id)
                for child in children:
                    if child.id == target_id:
                        return True
                    if await _is_descendant(child.id, target_id):
                        return True
                return False

            if await _is_descendant(card_id, data.parent_id):
                raise BadRequestException(detail="Cannot create a circular hierarchy")
        else:
            # parent_id를 None으로 설정 시 독립 가능 여부 확인
            if card_type not in app_config.independent_types:
                raise BadRequestException(
                    detail=f"A {card_type} card must have a parent"
                )

        card.parent_id = data.parent_id

    # 새 parent 기준으로 siblings 조회 (position 오름차순, 자기 자신 제외)
    siblings = await card_repo.get_siblings(card.project_id, data.parent_id, card_id)

    # after_card_id 기준으로 삽입 위치(position) 계산
    if data.after_card_id is None:
        # 첫 번째 위치에 삽입
        if siblings:
            first_pos = siblings[0].position
            new_position = first_pos // 2 if first_pos > 1 else first_pos - app_config.position_gap
        else:
            new_position = app_config.position_gap
    else:
        after_idx = next((i for i, s in enumerate(siblings) if s.id == data.after_card_id), None)
        if after_idx is None:
            # after_card_id가 siblings에 없으면 맨 끝에 배치
            new_position = (siblings[-1].position if siblings else 0) + app_config.position_gap
        elif after_idx == len(siblings) - 1:
            # after_card_id가 마지막 sibling이면 그 뒤에 추가
            new_position = siblings[after_idx].position + app_config.position_gap
        else:
            # 두 sibling 사이에 삽입
            prev_pos = siblings[after_idx].position
            next_pos = siblings[after_idx + 1].position
            new_position = (prev_pos + next_pos) // 2

            # gap이 너무 작으면 siblings 전체를 재정렬 후 재계산
            if next_pos - prev_pos < 2:
                for idx, s in enumerate(siblings):
                    s.position = (idx + 1) * app_config.position_gap
                await db.flush()
                prev_pos = siblings[after_idx].position
                if after_idx + 1 < len(siblings):
                    next_pos = siblings[after_idx + 1].position
                    new_position = (prev_pos + next_pos) // 2
                else:
                    new_position = prev_pos + app_config.position_gap

    card.position = new_position
    await db.flush()
    await db.refresh(card)

    return await _to_response_with_parents(db, card)
