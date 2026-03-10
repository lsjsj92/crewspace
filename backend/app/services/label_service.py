from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.base import ConflictException, NotFoundException
from app.models.label import Label
from app.schemas.label import LabelCreateRequest, LabelResponse, LabelUpdateRequest
from app.utils.datetime_utils import now_kst


async def get_project_labels(
    db: AsyncSession,
    project_id: UUID,
) -> list[LabelResponse]:
    """Get all labels for a project."""
    result = await db.execute(
        select(Label).where(
            Label.project_id == project_id,
            Label.deleted_at.is_(None),
        )
    )
    labels = list(result.scalars().all())
    return [LabelResponse.model_validate(l) for l in labels]


async def create_label(
    db: AsyncSession,
    project_id: UUID,
    data: LabelCreateRequest,
) -> LabelResponse:
    """Create a new label in the project."""
    # Check for duplicate name
    existing = await db.execute(
        select(Label).where(
            Label.project_id == project_id,
            Label.name == data.name,
            Label.deleted_at.is_(None),
        )
    )
    if existing.scalar_one_or_none():
        raise ConflictException(detail="A label with this name already exists")

    label = Label(
        project_id=project_id,
        name=data.name,
        color=data.color,
    )
    db.add(label)
    await db.flush()
    await db.refresh(label)

    return LabelResponse.model_validate(label)


async def update_label(
    db: AsyncSession,
    label_id: UUID,
    data: LabelUpdateRequest,
) -> LabelResponse:
    """Update a label."""
    result = await db.execute(
        select(Label).where(Label.id == label_id, Label.deleted_at.is_(None))
    )
    label = result.scalar_one_or_none()
    if not label:
        raise NotFoundException(detail="Label not found")

    update_data = data.model_dump(exclude_unset=True)

    # Check for duplicate name if name is being changed
    if "name" in update_data and update_data["name"] is not None:
        existing = await db.execute(
            select(Label).where(
                Label.project_id == label.project_id,
                Label.name == update_data["name"],
                Label.id != label_id,
                Label.deleted_at.is_(None),
            )
        )
        if existing.scalar_one_or_none():
            raise ConflictException(detail="A label with this name already exists")

    for key, value in update_data.items():
        setattr(label, key, value)

    await db.flush()
    await db.refresh(label)

    return LabelResponse.model_validate(label)


async def delete_label(
    db: AsyncSession,
    label_id: UUID,
) -> None:
    """Soft-delete a label."""
    result = await db.execute(
        select(Label).where(Label.id == label_id, Label.deleted_at.is_(None))
    )
    label = result.scalar_one_or_none()
    if not label:
        raise NotFoundException(detail="Label not found")

    label.deleted_at = now_kst()
    await db.flush()
