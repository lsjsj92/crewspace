# backend/app/services/weekly_service.py
# 주간 뷰 비즈니스 로직 서비스

from __future__ import annotations

import logging
import uuid
from datetime import date, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.card import Card, CardType
from app.models.user import User
from app.repositories.weekly_repository import WeeklyRepository
from app.schemas.weekly import (
    ActiveProjectItem,
    MonthlyGoalGroup,
    MonthlyGoalSubItem,
    WeeklyCardItem,
    WeeklyViewResponse,
)
from app.utils.datetime_utils import now_kst

logger = logging.getLogger(__name__)


def _get_week_monday(reference_date: date) -> date:
    """기준 날짜가 속한 주의 월요일을 반환한다."""
    return reference_date - timedelta(days=reference_date.weekday())


def _determine_card_status(
    card: Card,
    first_column_id: uuid.UUID | None,
    today: date,
) -> str:
    """카드의 현재 상태를 판별한다.

    우선순위: 취소 > 완료 > 지연 > 대기중 > 진행중
    """
    if card.cancelled_at is not None:
        return "취소"
    if card.completed_at is not None:
        return "완료"
    if card.due_date is not None and card.due_date < today:
        return "지연"
    if first_column_id is not None and card.column_id == first_column_id:
        return "대기중"
    return "진행중"


def _extract_hierarchy_titles(card: Card) -> tuple[str | None, str | None]:
    """카드의 계층 구조에서 Epic/Story 제목을 추출한다.

    반환: (epic_title, story_title)
    - task/sub_task의 경우 부모 체인을 따라 Epic/Story를 탐색한다
    - story의 경우 부모 Epic 제목만 반환한다
    - epic의 경우 (None, None)을 반환한다
    """
    card_type_value = card.card_type.value if hasattr(card.card_type, "value") else card.card_type

    if card_type_value == "epic":
        return None, None

    if card_type_value == "story":
        if card.parent is not None:
            return card.parent.title, None
        return None, None

    # task 또는 sub_task: 부모 체인 탐색
    parent = card.parent
    if parent is None:
        return None, None

    parent_type = parent.card_type.value if hasattr(parent.card_type, "value") else parent.card_type

    if parent_type == "epic":
        return parent.title, None

    if parent_type == "story":
        story_title = parent.title
        grandparent = parent.parent
        if grandparent is not None:
            return grandparent.title, story_title
        return None, story_title

    return None, None


def _get_card_type_value(card: Card) -> str:
    """카드 타입 열거형 값을 문자열로 반환한다."""
    return card.card_type.value if hasattr(card.card_type, "value") else card.card_type


def _build_weekly_card_item(
    card: Card,
    status: str,
    project_name: str,
) -> WeeklyCardItem:
    """카드 정보로 WeeklyCardItem을 생성한다."""
    epic_title, story_title = _extract_hierarchy_titles(card)
    card_type = _get_card_type_value(card)

    return WeeklyCardItem(
        epic_title=epic_title,
        story_title=story_title,
        task_title=card.title,
        card_type=card_type,
        due_date=card.due_date,
        status=status,
        project_name=project_name,
    )


async def _build_monthly_goals(
    repo: WeeklyRepository,
    user_id: uuid.UUID,
    today: date,
) -> list[MonthlyGoalGroup]:
    """월간 목표 섹션을 구성한다.

    사용자가 멤버인 활성 프로젝트의 Epic과 하위 Story/Task를 수집한다.
    """
    projects = await repo.get_user_member_projects(user_id)
    goals: list[MonthlyGoalGroup] = []

    for project in projects:
        epic_cards = await repo.get_project_epic_cards(project.id)
        if not epic_cards:
            continue

        first_col_id = await repo.get_project_first_column_id(project.id)

        for epic in epic_cards:
            items: list[MonthlyGoalSubItem] = []

            for child in epic.children:
                # 삭제/아카이브된 하위 카드는 제외
                if child.deleted_at is not None or child.archived_at is not None:
                    continue

                status = _determine_card_status(child, first_col_id, today)
                items.append(
                    MonthlyGoalSubItem(
                        title=child.title,
                        card_type=_get_card_type_value(child),
                        status=status,
                    )
                )

            if items:
                goals.append(
                    MonthlyGoalGroup(
                        epic_title=epic.title,
                        project_name=project.name,
                        items=items,
                    )
                )

    return goals


async def _build_active_projects(
    repo: WeeklyRepository,
    assigned_cards: list[Card],
) -> list[ActiveProjectItem]:
    """진행해야 할 프로젝트 섹션을 구성한다.

    사용자에게 할당된 카드가 있는 프로젝트의 Epic 목록을 수집한다.
    Epic 카드 자체가 할당된 경우와 하위 카드에서 Epic을 추적하는 경우를 모두 포함한다.
    """
    seen: set[tuple[str, str]] = set()
    result: list[ActiveProjectItem] = []

    for card in assigned_cards:
        project_name = card.project.name if card.project else ""
        card_type = _get_card_type_value(card)

        if card_type == "epic":
            key = (project_name, card.title)
            if key not in seen:
                seen.add(key)
                result.append(
                    ActiveProjectItem(
                        project_name=project_name,
                        epic_title=card.title,
                    )
                )
        else:
            # 부모 체인에서 Epic을 찾는다
            epic_title = _find_epic_title(card)
            if epic_title:
                key = (project_name, epic_title)
                if key not in seen:
                    seen.add(key)
                    result.append(
                        ActiveProjectItem(
                            project_name=project_name,
                            epic_title=epic_title,
                        )
                    )

    return result


def _find_epic_title(card: Card) -> str | None:
    """카드 부모 체인을 탐색하여 Epic 제목을 반환한다."""
    current = card.parent
    while current is not None:
        current_type = current.card_type.value if hasattr(current.card_type, "value") else current.card_type
        if current_type == "epic":
            return current.title
        current = current.parent
    return None


def _is_last_week_card(
    card: Card,
    last_week_start: date,
    last_week_end: date,
    end_column_ids: list[uuid.UUID],
) -> bool:
    """카드가 지난 주 목표에 해당하는지 판별한다.

    조건 (OR):
    1. due_date가 지난주 범위에 포함된 경우
    2. 현재 비종료 컬럼에 있고 created_at이 지난주 금요일 이전인 경우
    3. 지난주 이후 완료된 카드 중 created_at이 지난주 금요일 이전인 경우
    """
    last_week_friday = last_week_start + timedelta(days=4)

    if card.due_date is not None:
        if last_week_start <= card.due_date <= last_week_end:
            return True

    created_date = card.created_at.date() if card.created_at else None
    if created_date is None:
        return False

    is_old_card = created_date <= last_week_friday

    if not is_old_card:
        return False

    # 비종료 컬럼에 현재 있는 경우
    if card.column_id not in end_column_ids:
        return True

    # 지난주 이후 완료된 경우
    if card.completed_at is not None:
        completed_date = card.completed_at.date()
        if completed_date >= last_week_start:
            return True

    return False


def _is_this_week_card(
    card: Card,
    this_week_start: date,
    this_week_end: date,
    end_column_ids: list[uuid.UUID],
    first_column_id: uuid.UUID | None,
) -> bool:
    """카드가 이번 주 목표에 해당하는지 판별한다.

    조건 (OR):
    1. due_date가 이번주 범위에 포함된 경우
    2. 현재 비종료/비시작 컬럼에 있는 경우(진행중 상태)
    """
    if card.due_date is not None:
        if this_week_start <= card.due_date <= this_week_end:
            return True

    # 진행중 상태: 비종료이면서 비시작 컬럼에 있는 경우
    is_in_end_column = card.column_id in end_column_ids
    is_in_first_column = first_column_id is not None and card.column_id == first_column_id

    if not is_in_end_column and not is_in_first_column:
        return True

    return False


async def get_weekly_view(
    db: AsyncSession,
    current_user: User,
    week_start: date | None = None,
) -> WeeklyViewResponse:
    """주간 뷰 데이터를 구성하여 반환한다.

    week_start가 없으면 KST 기준 이번 주 월요일을 기본값으로 사용한다.
    """
    today = now_kst().date()

    # 기준 주의 월요일/일요일 계산
    if week_start is None:
        week_start = _get_week_monday(today)
    else:
        # 전달된 날짜가 해당 주의 월요일이 되도록 보정
        week_start = _get_week_monday(week_start)

    week_end = week_start + timedelta(days=6)
    last_week_start = week_start - timedelta(weeks=1)
    last_week_end = week_start - timedelta(days=1)

    logger.info(
        "주간 뷰 조회 - 사용자: %s, 기준 주: %s ~ %s",
        current_user.id,
        week_start,
        week_end,
    )

    repo = WeeklyRepository(db)

    # 사용자에게 할당된 카드 일괄 조회
    assigned_cards = await repo.get_assigned_cards_with_relations(current_user.id)

    # 프로젝트별 컬럼 정보 캐싱 (N+1 쿼리 방지)
    project_ids = {card.project_id for card in assigned_cards}
    first_col_cache: dict[uuid.UUID, uuid.UUID | None] = {}
    end_col_cache: dict[uuid.UUID, list[uuid.UUID]] = {}

    for project_id in project_ids:
        first_col_cache[project_id] = await repo.get_project_first_column_id(project_id)
        end_col_cache[project_id] = await repo.get_project_end_column_ids(project_id)

    # 월간 목표 구성
    monthly_goals = await _build_monthly_goals(repo, current_user.id, today)

    # 진행해야 할 프로젝트 구성
    active_projects = await _build_active_projects(repo, assigned_cards)

    # 지난 주 / 이번 주 목표 카드 분류
    last_week_items: list[WeeklyCardItem] = []
    this_week_items: list[WeeklyCardItem] = []

    for card in assigned_cards:
        project_name = card.project.name if card.project else ""
        first_col_id = first_col_cache.get(card.project_id)
        end_col_ids = end_col_cache.get(card.project_id, [])
        status = _determine_card_status(card, first_col_id, today)

        if _is_last_week_card(card, last_week_start, last_week_end, end_col_ids):
            last_week_items.append(
                _build_weekly_card_item(card, status, project_name)
            )

        if _is_this_week_card(card, week_start, week_end, end_col_ids, first_col_id):
            this_week_items.append(
                _build_weekly_card_item(card, status, project_name)
            )

    logger.info(
        "주간 뷰 구성 완료 - 지난주 카드: %d개, 이번주 카드: %d개",
        len(last_week_items),
        len(this_week_items),
    )

    return WeeklyViewResponse(
        week_start=week_start,
        week_end=week_end,
        month=week_start.month,
        monthly_goals=monthly_goals,
        active_projects=active_projects,
        last_week_items=last_week_items,
        this_week_items=this_week_items,
    )
