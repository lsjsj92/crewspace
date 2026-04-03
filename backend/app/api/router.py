# backend/app/api/router.py
# API v1 라우터 통합 모듈

from fastapi import APIRouter

from app.api.v1 import auth, boards, cards, comments, dashboard, labels, outcomes, projects, search, teams, users, weekly

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(teams.router, prefix="/teams", tags=["teams"])
api_router.include_router(projects.router, tags=["projects"])
api_router.include_router(boards.router, tags=["boards"])
api_router.include_router(cards.router, tags=["cards"])
api_router.include_router(comments.router, tags=["comments"])
api_router.include_router(labels.router, tags=["labels"])
api_router.include_router(outcomes.router, tags=["outcomes"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(search.router, tags=["search"])
api_router.include_router(weekly.router, prefix="/weekly", tags=["weekly"])
