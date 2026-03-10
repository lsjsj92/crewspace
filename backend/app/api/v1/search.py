from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.database import get_db
from app.models.user import User
from app.services import search_service

router = APIRouter()


@router.get("/search")
async def search(
    q: str = Query(..., min_length=1, description="Search query string"),
    type: str | None = Query(None, description="Filter by type: 'project' or 'card'"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Search across projects and cards.

    Searches project names/descriptions and card titles/descriptions
    that the current user has access to via team membership.

    - **q**: Search keyword (required, min 1 character)
    - **type**: Optional filter — 'project' or 'card'
    """
    results = await search_service.search(
        db=db,
        query=q,
        type_filter=type,
        current_user=current_user,
    )
    return {"results": results, "query": q, "type": type}
