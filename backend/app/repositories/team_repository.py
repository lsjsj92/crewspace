from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.team import Team, TeamMember, TeamRole
from app.repositories.base_repository import BaseRepository


class TeamRepository(BaseRepository[Team]):
    """Repository for Team-specific database operations."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Team, session)

    async def get_user_teams(self, user_id: UUID) -> list[Team]:
        """Fetch all teams where the user is a member."""
        result = await self.session.execute(
            select(Team)
            .join(TeamMember, Team.id == TeamMember.team_id)
            .where(TeamMember.user_id == user_id)
            .where(Team.deleted_at.is_(None))
        )
        return list(result.scalars().all())

    async def get_team_members(self, team_id: UUID) -> list[TeamMember]:
        """Fetch all members of a team with User relationship loaded."""
        result = await self.session.execute(
            select(TeamMember)
            .options(selectinload(TeamMember.user))
            .where(TeamMember.team_id == team_id)
        )
        return list(result.scalars().all())

    async def get_member(self, team_id: UUID, user_id: UUID) -> TeamMember | None:
        """Fetch a specific team member."""
        result = await self.session.execute(
            select(TeamMember)
            .options(selectinload(TeamMember.user))
            .where(TeamMember.team_id == team_id)
            .where(TeamMember.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def add_member(self, team_id: UUID, user_id: UUID, role: TeamRole) -> TeamMember:
        """Add a user as a member of a team."""
        member = TeamMember(team_id=team_id, user_id=user_id, role=role)
        self.session.add(member)
        await self.session.flush()
        await self.session.refresh(member)
        return member

    async def update_member_role(
        self, team_id: UUID, user_id: UUID, role: TeamRole
    ) -> TeamMember | None:
        """Update the role of a team member."""
        await self.session.execute(
            update(TeamMember)
            .where(TeamMember.team_id == team_id)
            .where(TeamMember.user_id == user_id)
            .values(role=role)
        )
        await self.session.flush()
        return await self.get_member(team_id, user_id)

    async def remove_member(self, team_id: UUID, user_id: UUID) -> bool:
        """Remove a member from a team. Returns True if a row was deleted."""
        result = await self.session.execute(
            delete(TeamMember)
            .where(TeamMember.team_id == team_id)
            .where(TeamMember.user_id == user_id)
        )
        await self.session.flush()
        return result.rowcount > 0
