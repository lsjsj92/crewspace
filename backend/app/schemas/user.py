from pydantic import BaseModel, EmailStr, Field

from app.schemas.auth import UserResponse


class UserUpdateRequest(BaseModel):
    display_name: str | None = Field(None, min_length=1, max_length=200)
    is_active: bool | None = None


class SelfProfileUpdateRequest(BaseModel):
    """사용자 본인 프로필 수정 요청"""
    display_name: str | None = Field(None, min_length=1, max_length=200)
    organization: str | None = None


class SelfPasswordChangeRequest(BaseModel):
    """사용자 본인 비밀번호 변경 요청"""
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=4)


class AdminUserUpdateRequest(BaseModel):
    email: EmailStr | None = None
    username: str | None = Field(None, min_length=1, max_length=100)
    display_name: str | None = Field(None, min_length=1, max_length=200)
    is_active: bool | None = None
    is_superadmin: bool | None = None
    employee_id: str | None = None
    organization: str | None = None
    gw_id: str | None = None


class UserListResponse(BaseModel):
    users: list[UserResponse]


class UserCreateRequest(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=1, max_length=100)
    display_name: str = Field(..., min_length=1, max_length=200)
    password: str = Field(..., min_length=4)
    employee_id: str | None = None
    organization: str | None = None
    gw_id: str | None = None


class UserPasswordResetRequest(BaseModel):
    new_password: str = Field(..., min_length=4)


class HRImportResponse(BaseModel):
    imported_count: int
    updated_count: int
    skipped_count: int
    team_created_count: int = 0
