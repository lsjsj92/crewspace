from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.base import ConflictException, NotFoundException
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import UserResponse
from app.schemas.user import UserUpdateRequest
from app.utils.security import hash_password


async def get_users(db: AsyncSession, skip: int = 0, limit: int = 100) -> list[UserResponse]:
    """Fetch a paginated list of all users."""
    user_repo = UserRepository(db)
    users = await user_repo.get_all(skip=skip, limit=limit)
    return [UserResponse.model_validate(u) for u in users]


async def update_user(db: AsyncSession, user_id: UUID, data: UserUpdateRequest) -> UserResponse:
    """Update user fields. Raises NotFoundException if user does not exist."""
    user_repo = UserRepository(db)
    update_data = data.model_dump(exclude_unset=True)
    if not update_data:
        user = await user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundException(detail="User not found")
        return UserResponse.model_validate(user)

    user = await user_repo.update(user_id, **update_data)
    if not user:
        raise NotFoundException(detail="User not found")
    return UserResponse.model_validate(user)


async def deactivate_user(db: AsyncSession, user_id: UUID) -> None:
    """Deactivate a user by setting is_active=False."""
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise NotFoundException(detail="User not found")
    await user_repo.update(user_id, is_active=False)


async def reset_password(db: AsyncSession, user_id: UUID, new_password: str) -> None:
    """Reset a user's password. Superadmin only."""
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise NotFoundException(detail="User not found")
    password_hash_val = hash_password(new_password)
    await user_repo.update(user_id, password_hash=password_hash_val)


async def create_user(
    db: AsyncSession,
    email: str,
    username: str,
    display_name: str,
    password: str,
    employee_id: str | None = None,
    organization: str | None = None,
    gw_id: str | None = None,
) -> UserResponse:
    """Create a new user. Used by admin."""
    user_repo = UserRepository(db)

    existing_email = await user_repo.get_by_email(email)
    if existing_email:
        raise ConflictException(detail="Email already registered")

    existing_username = await user_repo.get_by_username(username)
    if existing_username:
        raise ConflictException(detail="Username already taken")

    password_hash_val = hash_password(password)
    user = await user_repo.create(
        email=email,
        username=username,
        display_name=display_name,
        password_hash=password_hash_val,
        employee_id=employee_id,
        organization=organization,
        gw_id=gw_id,
    )
    return UserResponse.model_validate(user)
