# backend/app/exceptions/handlers.py
# FastAPI 전역 예외 핸들러 등록 (애플리케이션 예외, DB 제약조건 위반, 검증 오류)
import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from app.exceptions.base import CrewspaceException

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    """FastAPI 애플리케이션에 전역 예외 핸들러를 등록한다."""

    @app.exception_handler(CrewspaceException)
    async def crewspace_exception_handler(
        request: Request, exc: CrewspaceException
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )

    # 제약조건 이름 → 사용자 친화적 에러 메시지 매핑
    _constraint_messages: dict[str, str] = {
        "uq_users_email_active": "이미 사용 중인 이메일 주소입니다.",
        "uq_users_username_active": "이미 사용 중인 사용자 이름입니다.",
        "uq_users_employee_id_active": "이미 등록된 사번입니다.",
        "uq_users_gw_id_active": "이미 등록된 그룹웨어 ID입니다.",
        "uq_projects_prefix_active": "이미 사용 중인 프로젝트 접두사입니다.",
        "uq_board_columns_project_position_active": "해당 위치에 이미 컬럼이 존재합니다.",
        "uq_cards_project_card_number_active": "이 프로젝트에 동일한 카드 번호가 이미 존재합니다.",
        "uq_labels_project_name_active": "이 프로젝트에 동일한 이름의 라벨이 이미 존재합니다.",
        "uq_team_members_team_user": "이미 팀에 소속된 사용자입니다.",
        "uq_project_members_project_user": "이미 프로젝트에 소속된 사용자입니다.",
        "uq_card_assignees_card_user": "이미 카드에 배정된 사용자입니다.",
        # 기존 constraint 이름 (migration 이전 호환)
        "users_email_key": "이미 사용 중인 이메일 주소입니다.",
        "users_username_key": "이미 사용 중인 사용자 이름입니다.",
        "users_employee_id_key": "이미 등록된 사번입니다.",
        "users_gw_id_key": "이미 등록된 그룹웨어 ID입니다.",
    }

    @app.exception_handler(IntegrityError)
    async def integrity_exception_handler(
        request: Request, exc: IntegrityError
    ) -> JSONResponse:
        """DB 제약조건 위반 시 409 Conflict를 반환한다."""
        logger.warning("Database integrity error: %s", exc.orig)
        error_msg = str(exc.orig).lower() if exc.orig else ""

        if "unique" in error_msg or "duplicate" in error_msg:
            # 제약조건 이름으로 구체적인 메시지 조회
            detail = "동일한 값을 가진 레코드가 이미 존재합니다."
            for constraint_name, message in _constraint_messages.items():
                if constraint_name in error_msg:
                    detail = message
                    break
            return JSONResponse(
                status_code=409,
                content={"detail": detail},
            )

        return JSONResponse(
            status_code=409,
            content={"detail": "데이터 충돌: 리소스가 이미 존재하거나 제약조건이 위반되었습니다."},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={"detail": exc.errors()},
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        logger.exception("Unhandled exception: %s", exc)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )
