# backend/app/api/v1/weekly.py
# 주간 뷰 API 엔드포인트

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.database import get_db
from app.models.user import User
from app.schemas.weekly import WeeklyViewResponse
from app.services import weekly_service

router = APIRouter()


@router.get("", response_model=WeeklyViewResponse)
async def get_weekly_view(
    week_start: date | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> WeeklyViewResponse:
    """현재 사용자의 주간 뷰 데이터를 조회한다.

    week_start를 지정하지 않으면 KST 기준 이번 주 월요일을 기본값으로 사용한다.
    week_start가 월요일이 아닌 경우 해당 날짜가 속한 주의 월요일로 자동 보정된다.
    """
    return await weekly_service.get_weekly_view(db, current_user, week_start)
