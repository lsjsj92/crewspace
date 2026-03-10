from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.project import Project, ProjectMember, ProjectRole, ProjectStatus
from app.models.card import Card, CardAssignee
from app.repositories.base_repository import BaseRepository


class ProjectMemberRepository(BaseRepository[ProjectMember]):
    """Repository for ProjectMember-specific database operations."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(ProjectMember, session)

    async def get_project_members(self, project_id: UUID) -> list[ProjectMember]:
        """Fetch all members of a project with user info."""
        result = await self.session.execute(
            select(ProjectMember)
            .options(selectinload(ProjectMember.user))
            .where(ProjectMember.project_id == project_id)
            .order_by(ProjectMember.joined_at)
        )
        return list(result.scalars().all())

    async def get_member(self, project_id: UUID, user_id: UUID) -> ProjectMember | None:
        """Fetch a specific project member."""
        result = await self.session.execute(
            select(ProjectMember).where(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def add_member(
        self, project_id: UUID, user_id: UUID, role: ProjectRole
    ) -> ProjectMember:
        """Add a member to a project."""
        member = ProjectMember(
            project_id=project_id,
            user_id=user_id,
            role=role,
        )
        self.session.add(member)
        await self.session.flush()
        await self.session.refresh(member)
        return member

    async def update_member_role(
        self, project_id: UUID, user_id: UUID, role: ProjectRole
    ) -> ProjectMember | None:
        """Update a project member's role."""
        member = await self.get_member(project_id, user_id)
        if member:
            member.role = role
            await self.session.flush()
            await self.session.refresh(member)
        return member

    async def remove_member(self, project_id: UUID, user_id: UUID) -> bool:
        """Remove a member from a project."""
        member = await self.get_member(project_id, user_id)
        if member:
            await self.session.delete(member)
            await self.session.flush()
            return True
        return False

    async def get_user_project_ids(self, user_id: UUID) -> list[UUID]:
        """Get all project IDs the user is a member of."""
        result = await self.session.execute(
            select(ProjectMember.project_id).where(
                ProjectMember.user_id == user_id
            )
        )
        return list(result.scalars().all())

    async def get_user_projects(
        self, user_id: UUID, status_filter: str | None = None
    ) -> list[Project]:
        """Get all projects the user is a member of."""
        stmt = (
            select(Project)
            .join(ProjectMember, ProjectMember.project_id == Project.id)
            .where(
                ProjectMember.user_id == user_id,
                Project.deleted_at.is_(None),
            )
        )
        if status_filter:
            stmt = stmt.where(Project.status == ProjectStatus(status_filter))
        else:
            stmt = stmt.where(Project.status != ProjectStatus.completed)
        stmt = stmt.order_by(Project.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_recent_projects(
        self, user_id: UUID, limit: int = 5
    ) -> list[Project]:
        """Get recent projects based on card activity or membership join date."""
        from sqlalchemy import func, case, desc

        # Subquery: latest card activity per project
        card_activity = (
            select(
                Card.project_id,
                func.max(Card.updated_at).label("last_activity"),
            )
            .join(CardAssignee, CardAssignee.card_id == Card.id, isouter=True)
            .where(Card.deleted_at.is_(None))
            .group_by(Card.project_id)
            .subquery()
        )

        stmt = (
            select(Project)
            .join(ProjectMember, ProjectMember.project_id == Project.id)
            .outerjoin(card_activity, card_activity.c.project_id == Project.id)
            .where(
                ProjectMember.user_id == user_id,
                Project.deleted_at.is_(None),
                Project.status == ProjectStatus.active,
            )
            .order_by(
                desc(func.coalesce(card_activity.c.last_activity, ProjectMember.joined_at))
            )
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
