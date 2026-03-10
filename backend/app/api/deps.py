from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.exceptions.base import ForbiddenException, UnauthorizedException
from app.models.user import User
from app.services.auth_service import get_current_user_from_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Extract and validate the current user from the Bearer token."""
    return await get_current_user_from_token(db, token)


async def get_current_active_user(
    user: User = Depends(get_current_user),
) -> User:
    """Ensure the current user is active."""
    if not user.is_active:
        raise UnauthorizedException(detail="Account is deactivated")
    return user


async def require_superadmin(
    user: User = Depends(get_current_active_user),
) -> User:
    """Ensure the current user is a superadmin."""
    if not user.is_superadmin:
        raise ForbiddenException(detail="Superadmin access required")
    return user
