from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.auth import UserResponse


class CommentCreateRequest(BaseModel):
    content: str = Field(..., min_length=1)


class CommentUpdateRequest(BaseModel):
    content: str = Field(..., min_length=1)


class CommentResponse(BaseModel):
    id: UUID
    card_id: UUID
    user_id: UUID
    content: str
    created_at: datetime
    updated_at: datetime
    user: UserResponse | None = None

    model_config = {"from_attributes": True}
