from datetime import datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.refresh_token import RefreshToken
from app.utils.datetime_utils import now_kst


class RefreshTokenRepository:
    """Repository for RefreshToken database operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_token(
        self, user_id: UUID, token_hash: str, expires_at: datetime
    ) -> RefreshToken:
        """Create and persist a new refresh token record."""
        token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        self.session.add(token)
        await self.session.flush()
        await self.session.refresh(token)
        return token

    async def get_by_token_hash(self, token_hash: str) -> RefreshToken | None:
        """Find a refresh token by its hash."""
        result = await self.session.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        return result.scalar_one_or_none()

    async def revoke_token(self, token_hash: str) -> bool:
        """Revoke a single refresh token. Returns True if found and revoked."""
        result = await self.session.execute(
            update(RefreshToken)
            .where(RefreshToken.token_hash == token_hash)
            .values(revoked_at=now_kst())
        )
        await self.session.flush()
        return result.rowcount > 0

    async def revoke_all_user_tokens(self, user_id: UUID) -> None:
        """Revoke all refresh tokens for a given user."""
        await self.session.execute(
            update(RefreshToken)
            .where(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked_at.is_(None),
            )
            .values(revoked_at=now_kst())
        )
        await self.session.flush()
