from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_app_config
from app.models.board_column import BoardColumn
from app.repositories.base_repository import BaseRepository


class BoardColumnRepository(BaseRepository[BoardColumn]):
    """Repository for BoardColumn-specific database operations."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(BoardColumn, session)

    async def get_project_columns(self, project_id: UUID) -> list[BoardColumn]:
        """Fetch all columns for a project, sorted by position."""
        result = await self.session.execute(
            select(BoardColumn)
            .where(
                BoardColumn.project_id == project_id,
                BoardColumn.deleted_at.is_(None),
            )
            .order_by(BoardColumn.position)
        )
        return list(result.scalars().all())

    async def create_default_columns(self, project_id: UUID) -> list[BoardColumn]:
        """설정 파일 기반으로 프로젝트 기본 칼럼을 생성한다."""
        app_config = get_app_config()
        default_columns = app_config.default_columns

        if not default_columns:
            # 설정 파일에 정의가 없을 경우 기본값 사용
            default_columns = [
                {"name": "대기", "position": 0, "is_end": False},
                {"name": "진행 중", "position": 1, "is_end": False},
                {"name": "완료", "position": 2, "is_end": True},
            ]

        columns: list[BoardColumn] = []
        for idx, col_def in enumerate(default_columns):
            column = await self.create(
                project_id=project_id,
                name=col_def["name"],
                position=col_def.get("position", idx),
                is_end=col_def.get("is_end", False),
                wip_limit=col_def.get("wip_limit"),
            )
            columns.append(column)

        return columns
