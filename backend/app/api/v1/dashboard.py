from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.database import get_db
from app.models.user import User
from app.schemas.dashboard import DashboardOverview, MyCardsResponse, TeamDashboard
from app.services import dashboard_service

router = APIRouter()


@router.get("/overview", response_model=DashboardOverview)
async def get_overview(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> DashboardOverview:
    """Get the dashboard overview for the current user."""
    return await dashboard_service.get_overview(db, current_user)


@router.get("/teams/{team_id}", response_model=TeamDashboard)
async def get_team_dashboard(
    team_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> TeamDashboard:
    """Get team dashboard with projects and card counts per column."""
    return await dashboard_service.get_team_dashboard(db, team_id, current_user)


@router.get("/my-cards", response_model=MyCardsResponse)
async def get_my_cards(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> MyCardsResponse:
    """Get all cards assigned to the current user."""
    return await dashboard_service.get_my_cards(db, current_user)
