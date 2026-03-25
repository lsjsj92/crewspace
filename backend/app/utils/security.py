# backend/app/utils/security.py
# 비밀번호 해싱, JWT 토큰 생성/검증 유틸리티
from datetime import datetime, timedelta, timezone

import bcrypt
from jose import jwt

from app.config import get_settings


def hash_password(password: str) -> str:
    """평문 비밀번호를 bcrypt로 해싱한다."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """평문 비밀번호와 bcrypt 해시를 비교 검증한다."""
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def create_access_token(data: dict) -> str:
    """만료 시간이 포함된 JWT 액세스 토큰을 생성한다."""
    settings = get_settings()
    to_encode = data.copy()
    expire = datetime.now(tz=timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(data: dict) -> str:
    """만료 시간이 포함된 JWT 리프레시 토큰을 생성한다."""
    settings = get_settings()
    to_encode = data.copy()
    expire = datetime.now(tz=timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict:
    """JWT 토큰을 디코딩하고 검증한다. 실패 시 JWTError 발생."""
    settings = get_settings()
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
