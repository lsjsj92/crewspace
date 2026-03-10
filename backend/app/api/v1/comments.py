from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.database import get_db
from app.models.user import User
from app.schemas.comment import CommentCreateRequest, CommentResponse, CommentUpdateRequest
from app.schemas.common import MessageResponse
from app.services import comment_service

router = APIRouter()


@router.get("/cards/{card_id}/comments", response_model=list[CommentResponse])
async def list_comments(
    card_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[CommentResponse]:
    """Get all comments for a card."""
    return await comment_service.get_card_comments(db, card_id)


@router.post("/cards/{card_id}/comments", response_model=CommentResponse, status_code=201)
async def create_comment(
    card_id: UUID,
    data: CommentCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> CommentResponse:
    """Create a new comment on a card."""
    return await comment_service.create_comment(db, card_id, data, current_user)


@router.patch("/comments/{comment_id}", response_model=CommentResponse)
async def update_comment(
    comment_id: UUID,
    data: CommentUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> CommentResponse:
    """Update a comment. Only the author can update."""
    return await comment_service.update_comment(db, comment_id, data, current_user)


@router.delete("/comments/{comment_id}", response_model=MessageResponse)
async def delete_comment(
    comment_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> MessageResponse:
    """Soft-delete a comment. Only the author or a superadmin can delete."""
    await comment_service.delete_comment(db, comment_id, current_user)
    return MessageResponse(message="Comment deleted successfully")
