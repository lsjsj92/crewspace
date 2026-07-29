# backend/app/repositories/card_repository.py
# 카드 데이터 접근 레포지토리

from uuid import UUID

from sqlalchemy import delete, select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Load, selectinload

from app.models.card import Card, CardAssignee, CardLink, CardPriority, CardType
from app.repositories.base_repository import BaseRepository


def _parent_chain_loader() -> Load:
    """상위 카드 체인(최대 3단계: sub_task -> task -> story -> epic) eager 로딩 옵션.

    자기참조 관계는 lazy="selectin"이어도 자동 eager 로딩되지 않으므로
    응답 직렬화 시 MissingGreenlet을 방지하려면 명시적으로 로딩해야 한다.
    """
    return selectinload(Card.parent).selectinload(Card.parent).selectinload(Card.parent)


class CardRepository(BaseRepository[Card]):
    """Repository for Card-specific database operations."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Card, session)

    async def get_project_cards(
        self,
        project_id: UUID,
        card_type: str | None = None,
        assignee_id: UUID | None = None,
        priority: str | None = None,
        include_archived: bool = False,
    ) -> list[Card]:
        """Fetch all cards for a project with optional filters.

        include_archived가 False이면 아카이브된 카드를 제외한다 (칸반 보드 기본 동작).
        타임라인 전체 조회 등에서는 True로 아카이브 카드까지 포함한다.
        """
        stmt = select(Card).where(
            Card.project_id == project_id,
            Card.deleted_at.is_(None),
        )

        if not include_archived:
            stmt = stmt.where(Card.archived_at.is_(None))

        if card_type is not None:
            stmt = stmt.where(Card.card_type == CardType(card_type))

        if priority is not None:
            stmt = stmt.where(Card.priority == CardPriority(priority))

        if assignee_id is not None:
            stmt = stmt.join(CardAssignee).where(CardAssignee.user_id == assignee_id)

        stmt = stmt.options(_parent_chain_loader()).order_by(Card.position)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_column_cards(self, column_id: UUID) -> list[Card]:
        """Fetch all non-archived cards in a column, sorted by position."""
        result = await self.session.execute(
            select(Card)
            .where(
                Card.column_id == column_id,
                Card.archived_at.is_(None),
                Card.deleted_at.is_(None),
            )
            .options(selectinload(Card.assignees), _parent_chain_loader())
            .order_by(Card.position)
        )
        return list(result.scalars().all())

    async def get_next_card_number(self, project_id: UUID) -> int:
        """Get the next sequential card number for a project."""
        result = await self.session.execute(
            select(func.max(Card.card_number)).where(Card.project_id == project_id)
        )
        max_number = result.scalar_one_or_none()
        return (max_number or 0) + 1

    async def get_children(self, card_id: UUID) -> list[Card]:
        """Fetch all child cards of a given card with their direct children, sorted by position."""
        result = await self.session.execute(
            select(Card)
            .where(
                Card.parent_id == card_id,
                Card.deleted_at.is_(None),
            )
            .options(selectinload(Card.children), _parent_chain_loader())
            .order_by(Card.position)
        )
        return list(result.scalars().all())

    async def find_by_title(
        self,
        project_id: UUID,
        title: str,
        card_type: str,
        exclude_card_id: UUID | None = None,
    ) -> list[Card]:
        """Find cards with the same title and type in the project."""
        stmt = select(Card).where(
            Card.project_id == project_id,
            Card.title == title,
            Card.card_type == CardType(card_type),
            Card.deleted_at.is_(None),
        )
        if exclude_card_id:
            stmt = stmt.where(Card.id != exclude_card_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_siblings(
        self,
        project_id: UUID,
        parent_id: UUID | None,
        exclude_card_id: UUID,
    ) -> list[Card]:
        """같은 parent_id를 가진 형제 카드 목록을 position 순으로 반환한다."""
        parent_filter = Card.parent_id == parent_id if parent_id is not None else Card.parent_id.is_(None)
        stmt = (
            select(Card)
            .where(
                Card.project_id == project_id,
                parent_filter,
                Card.id != exclude_card_id,
                Card.deleted_at.is_(None),
                Card.archived_at.is_(None),
            )
            .order_by(Card.position)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_card_with_details(self, card_id: UUID) -> Card | None:
        """Fetch a card with all relationships loaded."""
        result = await self.session.execute(
            select(Card)
            .where(Card.id == card_id)
            .options(
                _parent_chain_loader(),
                selectinload(Card.assignees),
                selectinload(Card.labels),
                selectinload(Card.children),
                selectinload(Card.comments),
            )
        )
        return result.scalar_one_or_none()

    async def get_card_with_parents(self, card_id: UUID) -> Card | None:
        """카드와 상위 카드 체인을 함께 로딩한다 (응답 직렬화용)."""
        result = await self.session.execute(
            select(Card)
            .where(Card.id == card_id)
            .options(_parent_chain_loader())
        )
        return result.scalar_one_or_none()

    async def get_linked_parents(self, card_id: UUID) -> list[Card]:
        """보조 연결(card_links)로 지정된 상위 카드 목록을 연결 순서대로 반환한다."""
        result = await self.session.execute(
            select(Card)
            .join(CardLink, CardLink.parent_id == Card.id)
            .where(CardLink.card_id == card_id, Card.deleted_at.is_(None))
            .order_by(CardLink.created_at)
        )
        return list(result.scalars().all())

    async def get_linked_children(self, card_id: UUID) -> list[Card]:
        """이 카드를 보조 상위로 연결한 자식 카드 목록을 position 순으로 반환한다."""
        result = await self.session.execute(
            select(Card)
            .join(CardLink, CardLink.card_id == Card.id)
            .where(CardLink.parent_id == card_id, Card.deleted_at.is_(None))
            .options(selectinload(Card.children), _parent_chain_loader())
            .order_by(Card.position)
        )
        return list(result.scalars().all())

    async def get_project_card_links(self, project_id: UUID) -> list[CardLink]:
        """프로젝트 내 유효한 카드의 보조 연결 목록을 반환한다 (WBS 일괄 조회용)."""
        result = await self.session.execute(
            select(CardLink)
            .join(Card, Card.id == CardLink.card_id)
            .where(Card.project_id == project_id, Card.deleted_at.is_(None))
        )
        return list(result.scalars().all())

    async def replace_links(self, card_id: UUID, parent_ids: list[UUID]) -> None:
        """카드의 보조 상위 연결을 전체 교체한다."""
        await self.session.execute(delete(CardLink).where(CardLink.card_id == card_id))
        for parent_id in parent_ids:
            self.session.add(CardLink(card_id=card_id, parent_id=parent_id))
        await self.session.flush()

    async def remove_link(self, card_id: UUID, parent_id: UUID) -> None:
        """특정 보조 상위 연결을 제거한다 (주 부모로 승격 시 중복 방지용)."""
        await self.session.execute(
            delete(CardLink).where(
                CardLink.card_id == card_id, CardLink.parent_id == parent_id
            )
        )
