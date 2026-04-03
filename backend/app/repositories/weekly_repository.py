# backend/app/repositories/weekly_repository.py
# 주간 뷰 데이터 접근 레이어

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.board_column import BoardColumn
from app.models.card import Card, CardAssignee, CardType
from app.models.project import Project, ProjectMember, ProjectStatus


class WeeklyRepository:
    """주간 뷰에 필요한 데이터를 조회하는 레포지토리."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_user_member_projects(self, user_id: uuid.UUID) -> list[Project]:
        """사용자가 멤버로 속한 활성 프로젝트 목록을 조회한다."""
        result = await self.session.execute(
            select(Project)
            .join(ProjectMember, ProjectMember.project_id == Project.id)
            .where(
                ProjectMember.user_id == user_id,
                Project.deleted_at.is_(None),
                Project.status == ProjectStatus.active,
            )
            .order_by(Project.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_assigned_cards_with_relations(
        self,
        user_id: uuid.UUID,
    ) -> list[Card]:
        """사용자에게 할당된 활성 카드를 부모/프로젝트 관계와 함께 조회한다."""
        result = await self.session.execute(
            select(Card)
            .join(CardAssignee, CardAssignee.card_id == Card.id)
            .where(
                CardAssignee.user_id == user_id,
                Card.deleted_at.is_(None),
                Card.archived_at.is_(None),
            )
            .options(
                selectinload(Card.parent).selectinload(Card.parent),
                selectinload(Card.project),
            )
        )
        return list(result.scalars().all())

    async def get_project_first_column_id(
        self, project_id: uuid.UUID
    ) -> uuid.UUID | None:
        """프로젝트의 첫 번째 컬럼(position=0) ID를 조회한다. 대기중 판별에 사용한다."""
        result = await self.session.execute(
            select(BoardColumn.id)
            .where(
                BoardColumn.project_id == project_id,
                BoardColumn.deleted_at.is_(None),
                BoardColumn.position == 0,
            )
        )
        return result.scalar_one_or_none()

    async def get_project_end_column_ids(
        self, project_id: uuid.UUID
    ) -> list[uuid.UUID]:
        """프로젝트의 종료 컬럼 ID 목록을 조회한다. 진행중/완료 판별에 사용한다."""
        result = await self.session.execute(
            select(BoardColumn.id)
            .where(
                BoardColumn.project_id == project_id,
                BoardColumn.deleted_at.is_(None),
                BoardColumn.is_end.is_(True),
            )
        )
        return list(result.scalars().all())

    async def get_project_epic_cards(self, project_id: uuid.UUID) -> list[Card]:
        """프로젝트의 활성 Epic 카드 목록을 조회한다."""
        result = await self.session.execute(
            select(Card)
            .where(
                Card.project_id == project_id,
                Card.card_type == CardType.epic,
                Card.deleted_at.is_(None),
                Card.archived_at.is_(None),
            )
            .options(
                selectinload(Card.children).selectinload(Card.children),
                selectinload(Card.project),
            )
            .order_by(Card.position)
        )
        return list(result.scalars().all())
