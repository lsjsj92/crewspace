import logging
from datetime import timedelta

from sqlalchemy import and_, update

from app.config import get_app_config
from app.database import async_session_factory
from app.models.card import Card
from app.utils.datetime_utils import now_kst

logger = logging.getLogger(__name__)


async def auto_archive_cards() -> None:
    """Archive cards that have been in end column for more than auto_archive_days.

    Cards with a completed_at timestamp older than the configured threshold
    and no existing archived_at are automatically archived.
    """
    config = get_app_config()
    archive_threshold = now_kst() - timedelta(days=config.auto_archive_days)

    async with async_session_factory() as session:
        stmt = (
            update(Card)
            .where(
                and_(
                    Card.completed_at.isnot(None),
                    Card.completed_at <= archive_threshold,
                    Card.archived_at.is_(None),
                )
            )
            .values(archived_at=now_kst())
        )
        result = await session.execute(stmt)
        await session.commit()

        archived_count = result.rowcount
        if archived_count > 0:
            logger.info("Auto-archived %d cards older than %d days", archived_count, config.auto_archive_days)
        else:
            logger.debug("No cards to auto-archive")
