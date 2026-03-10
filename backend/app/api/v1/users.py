from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, require_superadmin
from app.database import get_db
from app.models.user import User
from app.schemas.auth import UserResponse
from app.schemas.common import MessageResponse
from app.schemas.user import (
    HRImportResponse,
    UserCreateRequest,
    UserListResponse,
    UserPasswordResetRequest,
    UserUpdateRequest,
)
from app.services import user_service

router = APIRouter()


@router.get("", response_model=UserListResponse)
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_superadmin),
) -> UserListResponse:
    """List all users. Superadmin only."""
    users = await user_service.get_users(db, skip=skip, limit=limit)
    return UserListResponse(users=users)


@router.post("", response_model=UserResponse, status_code=201)
async def create_user(
    data: UserCreateRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_superadmin),
) -> UserResponse:
    """Create a new user. Superadmin only."""
    return await user_service.create_user(
        db,
        email=data.email,
        username=data.username,
        display_name=data.display_name,
        password=data.password,
        employee_id=data.employee_id,
        organization=data.organization,
        gw_id=data.gw_id,
    )


@router.post("/hr-import", response_model=HRImportResponse)
async def hr_import(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_superadmin),
) -> HRImportResponse:
    """Import users from HR Excel file. Superadmin only."""
    from app.services.hr_service import import_from_excel
    result = await import_from_excel(db, current_user=current_user)
    return HRImportResponse(**result)


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    data: UserUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> UserResponse:
    """Update a user's profile."""
    return await user_service.update_user(db, user_id, data)


@router.patch("/{user_id}/password", response_model=MessageResponse)
async def reset_user_password(
    user_id: UUID,
    data: UserPasswordResetRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_superadmin),
) -> MessageResponse:
    """Reset a user's password. Superadmin only."""
    await user_service.reset_password(db, user_id, data.new_password)
    return MessageResponse(message="Password updated successfully")


@router.delete("/{user_id}", response_model=MessageResponse)
async def deactivate_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> MessageResponse:
    """Deactivate a user account."""
    await user_service.deactivate_user(db, user_id)
    return MessageResponse(message="User deactivated successfully")
