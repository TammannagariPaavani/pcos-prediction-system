"""Authentication and password security helpers."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.models import RoleEnum


password_context = CryptContext(
    schemes=["pbkdf2_sha256", "bcrypt"],
    deprecated="auto",
)


def hash_password(password: str) -> str:
    """Hash a plaintext password."""

    return password_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against its hash."""

    return password_context.verify(plain_password, hashed_password)


def _build_token(subject: str, role: RoleEnum, token_type: str, expires_delta: timedelta) -> str:
    """Create a signed JWT for the given user and token type."""

    expires_at = datetime.now(timezone.utc) + expires_delta
    payload = {
        "sub": subject,
        "role": role.value,
        "token_type": token_type,
        "exp": expires_at,
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(subject: str, role: RoleEnum) -> str:
    """Create a short-lived access token."""

    return _build_token(
        subject=subject,
        role=role,
        token_type="access",
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
    )


def create_refresh_token(subject: str, role: RoleEnum) -> str:
    """Create a long-lived refresh token."""

    return _build_token(
        subject=subject,
        role=role,
        token_type="refresh",
        expires_delta=timedelta(days=settings.refresh_token_expire_days),
    )


def decode_token(token: str) -> dict:
    """Decode and validate a JWT."""

    return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])


def get_cookie_max_age(token_type: str) -> int:
    """Return max-age in seconds for the requested cookie type."""

    if token_type == "access":
        return settings.access_token_expire_minutes * 60
    return settings.refresh_token_expire_days * 24 * 60 * 60
