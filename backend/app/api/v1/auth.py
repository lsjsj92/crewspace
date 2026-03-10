# backend/app/api/v1/auth.py
# 인증 관련 API 엔드포인트 (로그인, 회원가입, 토큰 갱신, 로그아웃, 현재 사용자 조회)
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.database import get_db
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.schemas.common import MessageResponse
from app.services import auth_service

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(
    data: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Register a new user account."""
    return await auth_service.register(db, data)


@router.post("/login", response_model=TokenResponse)
async def login(
    data: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Authenticate and receive access + refresh tokens."""
    return await auth_service.login(db, data)


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_active_user),
) -> UserResponse:
    """현재 로그인한 사용자 정보를 반환한다."""
    return UserResponse.model_validate(current_user)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    data: RefreshRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Rotate a refresh token for new access + refresh tokens."""
    return await auth_service.refresh_token(db, data)


@router.post("/logout", response_model=MessageResponse)
async def logout(
    data: RefreshRequest,
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """Revoke a refresh token (logout)."""
    await auth_service.logout(db, data.refresh_token)
    return MessageResponse(message="Successfully logged out")
