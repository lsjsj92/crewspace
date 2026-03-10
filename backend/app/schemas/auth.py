from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=1, max_length=100)
    display_name: str = Field(..., min_length=1, max_length=200)
    password: str = Field(..., min_length=8)


class LoginRequest(BaseModel):
    email: str = Field(..., min_length=1)
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    id: UUID
    email: str
    username: str
    display_name: str
    is_active: bool
    is_superadmin: bool
    created_at: datetime
    employee_id: str | None = None
    organization: str | None = None
    gw_id: str | None = None

    model_config = {"from_attributes": True}
