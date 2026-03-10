from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.comment import CardComment
from app.repositories.base_repository import BaseRepository


class CommentRepository(BaseRepository[CardComment]):
    """Repository for CardComment-specific database operations."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(CardComment, session)

    async def get_card_comments(self, card_id: UUID) -> list[CardComment]:
        """Fetch all comments for a card, sorted by created_at ascending."""
        result = await self.session.execute(
            select(CardComment)
            .where(
                CardComment.card_id == card_id,
                CardComment.deleted_at.is_(None),
            )
            .order_by(CardComment.created_at.asc())
        )
        return list(result.scalars().all())
