from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.card import Card, CardType, CardPriority
from app.repositories.base_repository import BaseRepository


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
    ) -> list[Card]:
        """Fetch all non-archived cards for a project with optional filters."""
        stmt = select(Card).where(
            Card.project_id == project_id,
            Card.archived_at.is_(None),
            Card.deleted_at.is_(None),
        )

        if card_type is not None:
            stmt = stmt.where(Card.card_type == CardType(card_type))

        if priority is not None:
            stmt = stmt.where(Card.priority == CardPriority(priority))

        if assignee_id is not None:
            from app.models.card import CardAssignee
            stmt = stmt.join(CardAssignee).where(CardAssignee.user_id == assignee_id)

        stmt = stmt.order_by(Card.position)
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
        """Fetch all child cards of a given card."""
        result = await self.session.execute(
            select(Card).where(
                Card.parent_id == card_id,
                Card.deleted_at.is_(None),
            )
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
                selectinload(Card.parent),
                selectinload(Card.assignees),
                selectinload(Card.labels),
                selectinload(Card.children),
                selectinload(Card.comments),
            )
        )
        return result.scalar_one_or_none()
