from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.repositories.base_repository import BaseRepository


class AuditRepository(BaseRepository[AuditLog]):
    """Repository for AuditLog CRUD operations."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(AuditLog, session)

    async def get_logs(
        self,
        user_id: UUID | None = None,
        team_id: UUID | None = None,
        project_id: UUID | None = None,
        card_id: UUID | None = None,
        action: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AuditLog]:
        """Get audit logs with optional filters."""
        stmt = select(AuditLog)

        if user_id is not None:
            stmt = stmt.where(AuditLog.user_id == user_id)
        if team_id is not None:
            stmt = stmt.where(AuditLog.team_id == team_id)
        if project_id is not None:
            stmt = stmt.where(AuditLog.project_id == project_id)
        if card_id is not None:
            stmt = stmt.where(AuditLog.card_id == card_id)
        if action is not None:
            stmt = stmt.where(AuditLog.action == action)

        stmt = stmt.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create_log(
        self,
        user_id: UUID,
        action: str,
        team_id: UUID | None = None,
        project_id: UUID | None = None,
        card_id: UUID | None = None,
        details: dict | None = None,
    ) -> AuditLog:
        """Create a new audit log entry."""
        return await self.create(
            user_id=user_id,
            action=action,
            team_id=team_id,
            project_id=project_id,
            card_id=card_id,
            details=details,
        )
