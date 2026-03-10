from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.base import ForbiddenException
from app.models.project import ProjectMember
from app.models.user import User
from app.repositories.project_member_repository import ProjectMemberRepository


async def check_project_permission(
    db: AsyncSession,
    project_id: UUID,
    user: User,
    required_roles: list[str],
) -> ProjectMember | None:
    """프로젝트 멤버십을 검증한다. superadmin은 우회한다."""
    if user.is_superadmin:
        return None
    repo = ProjectMemberRepository(db)
    member = await repo.get_member(project_id, user.id)
    if not member:
        raise ForbiddenException(detail="Not a member of this project")
    if member.role.value not in required_roles:
        raise ForbiddenException(detail="Insufficient project role")
    return member
