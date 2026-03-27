from typing import Generic, Type, TypeVar
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Base
from app.utils.datetime_utils import now_kst

T = TypeVar("T", bound=Base)


class BaseRepository(Generic[T]):
    """Generic base repository providing common CRUD operations."""

    def __init__(self, model: Type[T], session: AsyncSession) -> None:
        self.model = model
        self.session = session

    async def get_by_id(self, id: UUID) -> T | None:
        """Fetch a single record by its primary key UUID.
        SoftDeleteMixin을 사용하는 모델은 deleted_at IS NULL 조건을 자동 적용한다.
        """
        stmt = select(self.model).where(self.model.id == id)
        if hasattr(self.model, "deleted_at"):
            stmt = stmt.where(self.model.deleted_at.is_(None))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[T]:
        """Fetch multiple records with pagination.
        SoftDeleteMixin을 사용하는 모델은 soft-deleted 행을 자동 제외한다.
        """
        stmt = select(self.model).offset(skip).limit(limit)
        if hasattr(self.model, "deleted_at"):
            stmt = stmt.where(self.model.deleted_at.is_(None))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create(self, **kwargs) -> T:
        """Create and persist a new record."""
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def update(self, id: UUID, **kwargs) -> T | None:
        """Update a record by ID. Returns the updated instance or None."""
        await self.session.execute(
            update(self.model).where(self.model.id == id).values(**kwargs)
        )
        await self.session.flush()
        return await self.get_by_id(id)

    async def soft_delete(self, id: UUID) -> bool:
        """Soft-delete a record by setting deleted_at. Returns True if found."""
        result = await self.session.execute(
            update(self.model)
            .where(self.model.id == id)
            .values(deleted_at=now_kst())
        )
        await self.session.flush()
        return result.rowcount > 0
