from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.board_column import BoardColumn
from app.models.card import Card, CardAssignee
from app.models.project import Project, ProjectMember, ProjectRole, ProjectStatus
from app.models.team import Team
from app.models.user import User
from app.schemas.dashboard import (
    CardWithProject,
    ColumnCardCount,
    DashboardOverview,
    MyCardsResponse,
    ProjectSummary,
    ProjectWithCounts,
    TeamDashboard,
)


async def get_overview(
    db: AsyncSession,
    current_user: User,
) -> DashboardOverview:
    """Get the dashboard overview for the current user."""
    if current_user.is_superadmin:
        # Superadmin sees all projects
        projects_result = await db.execute(
            select(Project).where(Project.deleted_at.is_(None))
        )
        projects = list(projects_result.scalars().all())
    else:
        # Get projects via membership
        projects_result = await db.execute(
            select(Project)
            .join(ProjectMember, ProjectMember.project_id == Project.id)
            .where(
                ProjectMember.user_id == current_user.id,
                Project.deleted_at.is_(None),
            )
        )
        projects = list(projects_result.scalars().all())

    total_projects = len(projects)
    total_active_projects = sum(1 for p in projects if p.status == ProjectStatus.active)

    # Get user's role in each project
    project_summaries = []
    for project in projects:
        my_role = None
        if not current_user.is_superadmin:
            member_result = await db.execute(
                select(ProjectMember.role).where(
                    ProjectMember.project_id == project.id,
                    ProjectMember.user_id == current_user.id,
                )
            )
            role = member_result.scalar_one_or_none()
            my_role = role.value if role else None

        status_val = project.status.value if isinstance(project.status, ProjectStatus) else project.status
        project_summaries.append(
            ProjectSummary(
                id=project.id,
                name=project.name,
                prefix=project.prefix,
                status=status_val,
                my_role=my_role,
            )
        )

    # 삭제/아카이브된 카드를 제외하고 현재 사용자에게 할당된 카드 수 조회
    my_cards_result = await db.execute(
        select(func.count(CardAssignee.id))
        .join(Card, Card.id == CardAssignee.card_id)
        .where(
            CardAssignee.user_id == current_user.id,
            Card.deleted_at.is_(None),
            Card.archived_at.is_(None),
        )
    )
    my_cards_count = my_cards_result.scalar_one()

    return DashboardOverview(
        total_projects=total_projects,
        total_active_projects=total_active_projects,
        my_cards_count=my_cards_count,
        projects=project_summaries,
    )


async def get_team_dashboard(
    db: AsyncSession,
    team_id: UUID,
    current_user: User,
) -> TeamDashboard:
    """Get the team dashboard with projects and card counts per column."""
    team_result = await db.execute(
        select(Team).where(Team.id == team_id, Team.deleted_at.is_(None))
    )
    team = team_result.scalar_one_or_none()
    if not team:
        from app.exceptions.base import NotFoundException
        raise NotFoundException(detail="Team not found")

    projects_result = await db.execute(
        select(Project).where(
            Project.team_id == team_id,
            Project.deleted_at.is_(None),
        ).order_by(Project.created_at.desc())
    )
    projects = list(projects_result.scalars().all())

    project_with_counts = []
    for project in projects:
        columns_result = await db.execute(
            select(BoardColumn).where(
                BoardColumn.project_id == project.id,
                BoardColumn.deleted_at.is_(None),
            ).order_by(BoardColumn.position)
        )
        columns = list(columns_result.scalars().all())

        column_counts = []
        for col in columns:
            card_count_result = await db.execute(
                select(func.count(Card.id)).where(
                    Card.column_id == col.id,
                    Card.deleted_at.is_(None),
                    Card.archived_at.is_(None),
                )
            )
            card_count = card_count_result.scalar_one()
            column_counts.append(
                ColumnCardCount(
                    column_id=col.id,
                    column_name=col.name,
                    card_count=card_count,
                )
            )

        status_val = project.status.value if isinstance(project.status, ProjectStatus) else project.status
        project_with_counts.append(
            ProjectWithCounts(
                id=project.id,
                name=project.name,
                prefix=project.prefix,
                status=status_val,
                columns=column_counts,
            )
        )

    return TeamDashboard(
        id=team.id,
        name=team.name,
        description=team.description,
        projects=project_with_counts,
    )


async def get_my_cards(
    db: AsyncSession,
    current_user: User,
) -> MyCardsResponse:
    """Get all cards assigned to the current user with project info."""
    stmt = (
        select(Card, Project.name.label("project_name"))
        .join(CardAssignee, CardAssignee.card_id == Card.id)
        .join(Project, Project.id == Card.project_id)
        .where(
            CardAssignee.user_id == current_user.id,
            Card.deleted_at.is_(None),
            Card.archived_at.is_(None),
        )
        .order_by(Card.created_at.desc())
    )

    result = await db.execute(stmt)
    rows = result.all()

    cards = []
    for row in rows:
        card = row[0]
        project_name = row[1]

        card_type = card.card_type.value if hasattr(card.card_type, "value") else card.card_type
        priority = card.priority.value if hasattr(card.priority, "value") else card.priority

        cards.append(
            CardWithProject(
                id=card.id,
                project_id=card.project_id,
                column_id=card.column_id,
                parent_id=card.parent_id,
                card_type=card_type,
                card_number=card.card_number,
                title=card.title,
                description=card.description,
                priority=priority,
                position=card.position,
                start_date=card.start_date,
                due_date=card.due_date,
                completed_at=card.completed_at,
                archived_at=card.archived_at,
                created_by=card.created_by,
                created_at=card.created_at,
                project_name=project_name,
            )
        )

    return MyCardsResponse(cards=cards)
