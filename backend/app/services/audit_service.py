from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.repositories.audit_repository import AuditRepository


async def log_action(
    db: AsyncSession,
    user_id: UUID,
    action: str,
    team_id: UUID | None = None,
    project_id: UUID | None = None,
    card_id: UUID | None = None,
    details: dict | None = None,
) -> None:
    """Create an audit log entry for a user action."""
    repo = AuditRepository(db)
    await repo.create_log(
        user_id=user_id,
        action=action,
        team_id=team_id,
        project_id=project_id,
        card_id=card_id,
        details=details,
    )


async def get_audit_logs(
    db: AsyncSession,
    user_id: UUID | None = None,
    team_id: UUID | None = None,
    project_id: UUID | None = None,
    card_id: UUID | None = None,
    action: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[AuditLog]:
    """Retrieve audit logs with optional filters."""
    repo = AuditRepository(db)
    return await repo.get_logs(
        user_id=user_id,
        team_id=team_id,
        project_id=project_id,
        card_id=card_id,
        action=action,
        limit=limit,
        offset=offset,
    )
