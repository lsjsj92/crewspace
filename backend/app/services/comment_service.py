from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.base import ForbiddenException, NotFoundException
from app.models.user import User
from app.repositories.comment_repository import CommentRepository
from app.schemas.comment import CommentCreateRequest, CommentResponse, CommentUpdateRequest
from app.utils.datetime_utils import now_kst


async def get_card_comments(
    db: AsyncSession,
    card_id: UUID,
) -> list[CommentResponse]:
    """Get all comments for a card."""
    repo = CommentRepository(db)
    comments = await repo.get_card_comments(card_id)
    return [CommentResponse.model_validate(c) for c in comments]


async def create_comment(
    db: AsyncSession,
    card_id: UUID,
    data: CommentCreateRequest,
    current_user: User,
) -> CommentResponse:
    """Create a new comment on a card."""
    repo = CommentRepository(db)
    comment = await repo.create(
        card_id=card_id,
        user_id=current_user.id,
        content=data.content,
    )
    return CommentResponse.model_validate(comment)


async def update_comment(
    db: AsyncSession,
    comment_id: UUID,
    data: CommentUpdateRequest,
    current_user: User,
) -> CommentResponse:
    """Update a comment. Only the author can update their own comment."""
    repo = CommentRepository(db)
    comment = await repo.get_by_id(comment_id)

    if not comment or comment.deleted_at is not None:
        raise NotFoundException(detail="Comment not found")

    if comment.user_id != current_user.id:
        raise ForbiddenException(detail="You can only edit your own comments")

    updated = await repo.update(comment_id, content=data.content)
    return CommentResponse.model_validate(updated)


async def delete_comment(
    db: AsyncSession,
    comment_id: UUID,
    current_user: User,
) -> None:
    """Soft-delete a comment. Only the author or a superadmin can delete."""
    repo = CommentRepository(db)
    comment = await repo.get_by_id(comment_id)

    if not comment or comment.deleted_at is not None:
        raise NotFoundException(detail="Comment not found")

    if comment.user_id != current_user.id and not current_user.is_superadmin:
        raise ForbiddenException(detail="You can only delete your own comments")

    await repo.soft_delete(comment_id)
