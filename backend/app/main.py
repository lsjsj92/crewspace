# backend/app/main.py
# Crewspace 백엔드 애플리케이션 진입점
import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import IntegrityError, OperationalError, ProgrammingError

from app.config import get_settings
from app.database import engine, async_session_factory
from app.api.router import api_router
from app.exceptions.handlers import register_exception_handlers
from app.middleware.logging_middleware import LoggingMiddleware
from app.tasks.scheduler import start_scheduler, stop_scheduler

logger = logging.getLogger(__name__)


async def _ensure_superadmin() -> None:
    """슈퍼관리자 계정을 .env 설정과 동기화한다.

    매 기동 시 .env의 이메일/비밀번호가 DB에 반영되도록 보장한다.
    다중 워커 환경에서 동시 실행되더라도 IntegrityError를 안전하게 처리한다.
    """
    settings = get_settings()
    from app.repositories.user_repository import UserRepository
    from app.utils.security import hash_password, verify_password

    async with async_session_factory() as session:
        repo = UserRepository(session)

        # 이메일 또는 username으로 기존 슈퍼관리자 조회
        admin = await repo.get_by_email(settings.SUPERADMIN_EMAIL)
        if not admin:
            admin = await repo.get_by_username(settings.SUPERADMIN_USERNAME)

        if admin and admin.is_superadmin:
            # .env 설정과 DB를 동기화
            changed = False
            if admin.email != settings.SUPERADMIN_EMAIL:
                admin.email = settings.SUPERADMIN_EMAIL
                changed = True
            if not verify_password(settings.SUPERADMIN_PASSWORD, admin.password_hash):
                admin.password_hash = hash_password(settings.SUPERADMIN_PASSWORD)
                changed = True
            if changed:
                await session.commit()
                logger.info("슈퍼관리자 설정 동기화 완료: %s", settings.SUPERADMIN_EMAIL)
            return

        # 계정이 없으면 신규 생성
        try:
            user = await repo.create(
                email=settings.SUPERADMIN_EMAIL,
                username=settings.SUPERADMIN_USERNAME,
                display_name=settings.SUPERADMIN_USERNAME,
                password_hash=hash_password(settings.SUPERADMIN_PASSWORD),
                is_active=True,
                is_superadmin=True,
            )
            await session.commit()
            logger.info("슈퍼관리자 계정 생성 완료: %s", user.email)
        except IntegrityError:
            await session.rollback()
            logger.info("슈퍼관리자 계정이 이미 존재합니다 (다른 워커에서 생성됨)")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Crewspace 서버 기동 중...")
    try:
        await _ensure_superadmin()
    except (ProgrammingError, OperationalError) as exc:
        logger.error(
            "슈퍼관리자 생성 실패 - 마이그레이션이 실행되었는지 확인하세요: %s",
            exc,
        )
        raise
    start_scheduler()
    yield
    stop_scheduler()
    await engine.dispose()
    logger.info("Crewspace 서버 종료 완료.")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Crewspace API",
        description="Self-hosted project management system",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(LoggingMiddleware)

    app.include_router(api_router, prefix="/api/v1")

    from app.websocket.handlers import router as ws_router
    app.include_router(ws_router)

    register_exception_handlers(app)

    return app


app = create_app()
