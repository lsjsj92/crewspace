from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.card import Card
from app.models.project import Project, ProjectMember
from app.models.user import User


async def _get_user_project_ids(db: AsyncSession, user_id: UUID) -> list[UUID]:
    """Get all project IDs the user is a member of."""
    stmt = select(ProjectMember.project_id).where(ProjectMember.user_id == user_id)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def _search_projects(
    db: AsyncSession, query: str, project_ids: list[UUID] | None
) -> list[dict]:
    """Search projects by name or description within accessible projects."""
    pattern = f"%{query}%"
    stmt = select(Project).where(
        Project.deleted_at.is_(None),
        (Project.name.ilike(pattern) | Project.description.ilike(pattern)),
    )
    if project_ids is not None:
        if not project_ids:
            return []
        stmt = stmt.where(Project.id.in_(project_ids))
    stmt = stmt.limit(20)
    result = await db.execute(stmt)
    projects = result.scalars().all()

    return [
        {
            "type": "project",
            "id": str(p.id),
            "title": p.name,
            "description": p.description,
            "team_id": str(p.team_id) if p.team_id else None,
            "status": p.status.value if p.status else None,
            "prefix": p.prefix,
        }
        for p in projects
    ]


async def _search_cards(
    db: AsyncSession, query: str, project_ids: list[UUID] | None
) -> list[dict]:
    """Search cards by title or description within accessible projects."""
    pattern = f"%{query}%"
    stmt = (
        select(Card)
        .join(Project, Card.project_id == Project.id)
        .where(
            Project.deleted_at.is_(None),
            Card.deleted_at.is_(None),
            (Card.title.ilike(pattern) | Card.description.ilike(pattern)),
        )
    )
    if project_ids is not None:
        if not project_ids:
            return []
        stmt = stmt.where(Project.id.in_(project_ids))
    stmt = stmt.limit(20)
    result = await db.execute(stmt)
    cards = result.scalars().all()

    return [
        {
            "type": "card",
            "id": str(c.id),
            "title": c.title,
            "description": c.description,
            "project_id": str(c.project_id),
            "card_number": c.card_number,
            "card_type": c.card_type.value if c.card_type else None,
            "priority": c.priority.value if c.priority else None,
        }
        for c in cards
    ]


async def search(
    db: AsyncSession,
    query: str,
    type_filter: str | None,
    current_user: User,
) -> list[dict]:
    """Search projects and cards the user has access to via project membership."""
    if current_user.is_superadmin:
        project_ids = None  # No filter for superadmin
    else:
        project_ids = await _get_user_project_ids(db, current_user.id)

    results: list[dict] = []

    if type_filter is None or type_filter == "project":
        results.extend(await _search_projects(db, query, project_ids))

    if type_filter is None or type_filter == "card":
        results.extend(await _search_cards(db, query, project_ids))

    return results
