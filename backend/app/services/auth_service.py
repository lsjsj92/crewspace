import hashlib
from datetime import datetime, timedelta, timezone

from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.exceptions.base import (
    BadRequestException,
    ConflictException,
    NotFoundException,
    UnauthorizedException,
)
from app.models.user import User
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.utils.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


def _hash_token(token: str) -> str:
    """Create a SHA-256 hash of a token string for storage."""
    return hashlib.sha256(token.encode()).hexdigest()


async def register(db: AsyncSession, data: RegisterRequest) -> UserResponse:
    """Register a new user. Raises ConflictException if email or username taken."""
    user_repo = UserRepository(db)

    if await user_repo.get_by_email(data.email):
        raise ConflictException(detail="Email already registered")

    if await user_repo.get_by_username(data.username):
        raise ConflictException(detail="Username already taken")

    user = await user_repo.create(
        email=data.email,
        username=data.username,
        display_name=data.display_name,
        password_hash=hash_password(data.password),
    )

    return UserResponse.model_validate(user)


async def login(db: AsyncSession, data: LoginRequest) -> TokenResponse:
    """Authenticate a user and return access + refresh tokens."""
    user_repo = UserRepository(db)
    user = await user_repo.get_by_email(data.email)

    if not user or not verify_password(data.password, user.password_hash):
        raise UnauthorizedException(detail="Invalid email or password")

    if not user.is_active:
        raise UnauthorizedException(detail="Account is deactivated")

    settings = get_settings()
    token_data = {"sub": str(user.id)}
    access_token = create_access_token(token_data)
    refresh_token_str = create_refresh_token(token_data)

    # Store refresh token hash
    token_repo = RefreshTokenRepository(db)
    expires_at = datetime.now(tz=timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    await token_repo.create_token(
        user_id=user.id,
        token_hash=_hash_token(refresh_token_str),
        expires_at=expires_at,
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token_str,
    )


async def refresh_token(db: AsyncSession, data: RefreshRequest) -> TokenResponse:
    """Rotate a refresh token: verify the old one, revoke it, and issue new tokens."""
    try:
        payload = decode_token(data.refresh_token)
    except JWTError:
        raise UnauthorizedException(detail="Invalid refresh token")

    if payload.get("type") != "refresh":
        raise UnauthorizedException(detail="Invalid token type")

    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedException(detail="Invalid token payload")

    token_repo = RefreshTokenRepository(db)
    old_hash = _hash_token(data.refresh_token)
    stored_token = await token_repo.get_by_token_hash(old_hash)

    if not stored_token or stored_token.revoked_at is not None:
        raise UnauthorizedException(detail="Refresh token revoked or not found")

    if stored_token.expires_at.replace(tzinfo=timezone.utc) < datetime.now(tz=timezone.utc):
        raise UnauthorizedException(detail="Refresh token expired")

    # Revoke old token
    await token_repo.revoke_token(old_hash)

    # Issue new tokens
    settings = get_settings()
    token_data = {"sub": user_id}
    new_access = create_access_token(token_data)
    new_refresh = create_refresh_token(token_data)

    expires_at = datetime.now(tz=timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    await token_repo.create_token(
        user_id=stored_token.user_id,
        token_hash=_hash_token(new_refresh),
        expires_at=expires_at,
    )

    return TokenResponse(
        access_token=new_access,
        refresh_token=new_refresh,
    )


async def logout(db: AsyncSession, refresh_token_str: str) -> None:
    """Revoke the given refresh token."""
    token_repo = RefreshTokenRepository(db)
    token_hash = _hash_token(refresh_token_str)
    await token_repo.revoke_token(token_hash)


async def get_current_user_from_token(db: AsyncSession, token: str) -> User:
    """Decode an access token and return the corresponding user."""
    try:
        payload = decode_token(token)
    except JWTError:
        raise UnauthorizedException(detail="Invalid access token")

    if payload.get("type") != "access":
        raise UnauthorizedException(detail="Invalid token type")

    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedException(detail="Invalid token payload")

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)

    if not user:
        raise NotFoundException(detail="User not found")

    if not user.is_active:
        raise UnauthorizedException(detail="Account is deactivated")

    return user
