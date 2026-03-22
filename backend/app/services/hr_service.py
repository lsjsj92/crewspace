from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_app_config
from app.models.team import Team, TeamMember, TeamRole
from app.models.user import User
from app.repositories.team_repository import TeamRepository
from app.repositories.user_repository import UserRepository
from app.utils.security import hash_password


async def _find_or_create_team(
    db: AsyncSession,
    team_repo: TeamRepository,
    org_name: str,
    creator_id,
) -> Team:
    """Find an existing team by name or create a new one."""
    result = await db.execute(
        select(Team).where(Team.name == org_name, Team.deleted_at.is_(None))
    )
    team = result.scalar_one_or_none()
    if team:
        return team

    team = await team_repo.create(
        name=org_name,
        description=f"Auto-created from HR import ({org_name})",
        created_by=creator_id,
    )
    await team_repo.add_member(team.id, creator_id, TeamRole.owner)
    return team


async def import_from_excel(
    db: AsyncSession,
    file_path: str | None = None,
    current_user: User | None = None,
) -> dict:
    """HR 엑셀 파일에서 사용자를 가져온다.

    조직(organization) 컬럼을 기반으로 팀을 자동 생성하고,
    해당 팀에 사용자를 멤버로 추가한다.

    Returns:
        dict with imported_count, updated_count, skipped_count, team_created_count
    """
    import openpyxl

    app_config = get_app_config()

    if file_path is None:
        file_path = app_config.hr_excel_path

    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"HR excel file not found: {file_path}")

    wb = openpyxl.load_workbook(path, read_only=True)
    ws = wb.active

    imported_count = 0
    updated_count = 0
    skipped_count = 0
    team_created_count = 0

    user_repo = UserRepository(db)
    team_repo = TeamRepository(db)

    # Cache for teams found/created during this import
    org_team_cache: dict[str, Team] = {}

    # Determine the creator for auto-generated teams
    creator_id = current_user.id if current_user else None
    if not creator_id:
        # Fallback: find a superadmin
        result = await db.execute(
            select(User).where(User.is_superadmin.is_(True)).limit(1)
        )
        admin = result.scalar_one_or_none()
        if admin:
            creator_id = admin.id

    rows = list(ws.iter_rows(min_row=2, values_only=True))
    for row in rows:
        if len(row) < 4:
            skipped_count += 1
            continue

        name, organization, employee_id, gw_id = row[0], row[1], row[2], row[3]

        if not name or not gw_id:
            skipped_count += 1
            continue

        employee_id = str(employee_id).strip() if employee_id else None
        gw_id = str(gw_id).strip()
        name = str(name).strip()
        organization = str(organization).strip() if organization else None

        # Check existing user by gw_id or employee_id
        existing_user = await user_repo.get_by_username(gw_id)

        if not existing_user and employee_id:
            result = await db.execute(
                select(User).where(User.employee_id == employee_id)
            )
            existing_user = result.scalar_one_or_none()

        if existing_user:
            existing_user.display_name = name
            if organization:
                existing_user.organization = organization
            if employee_id:
                existing_user.employee_id = employee_id
            existing_user.gw_id = gw_id
            await db.flush()
            user_for_team = existing_user
            updated_count += 1
        else:
            email = f"{gw_id}@crewspace.local"
            default_password = app_config.hr_default_password
            password_hash_val = hash_password(default_password)

            new_user = User(
                email=email,
                username=gw_id,
                display_name=name,
                password_hash=password_hash_val,
                employee_id=employee_id,
                organization=organization,
                gw_id=gw_id,
                is_active=True,
            )
            db.add(new_user)
            await db.flush()
            user_for_team = new_user
            imported_count += 1

        # Auto-create team from organization and add user as member
        if organization and creator_id:
            if organization not in org_team_cache:
                team = await _find_or_create_team(
                    db, team_repo, organization, creator_id
                )
                is_new = team.created_at == team.updated_at if hasattr(team, 'updated_at') else False
                org_team_cache[organization] = team

            team = org_team_cache[organization]
            existing_member = await team_repo.get_member(team.id, user_for_team.id)
            if not existing_member:
                await team_repo.add_member(
                    team.id, user_for_team.id, TeamRole.member
                )

    wb.close()

    # Count how many teams were newly created in this run
    team_created_count = len(org_team_cache)

    return {
        "imported_count": imported_count,
        "updated_count": updated_count,
        "skipped_count": skipped_count,
        "team_created_count": team_created_count,
    }
