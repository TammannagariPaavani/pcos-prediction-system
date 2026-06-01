"""Authentication and user schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models import RoleEnum
from app.schemas.common import ORMModel


class OrganizationSummary(ORMModel):
    """Public organization representation."""

    id: str
    name: str
    slug: str
    is_active: bool


class UserCreate(BaseModel):
    """Payload used to register a new user."""

    full_name: str = Field(min_length=2, max_length=255)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: RoleEnum
    organization_name: str | None = Field(default=None, min_length=2, max_length=255)

    @field_validator("organization_name", mode="before")
    @classmethod
    def normalize_organization_name(cls, value: str | None) -> str | None:
        """Treat blank organization names as missing values."""

        if value is None:
            return None
        if isinstance(value, str):
            normalized = value.strip()
            return normalized or None
        return value


class UserLogin(BaseModel):
    """Payload used to authenticate a user."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class TokenPair(BaseModel):
    """JWT token response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Decoded JWT token contents."""

    sub: str
    role: RoleEnum
    token_type: str
    exp: int


class UserSummary(ORMModel):
    """Public user representation."""

    id: str
    full_name: str
    email: EmailStr
    role: RoleEnum
    is_active: bool
    created_at: datetime
    organization: OrganizationSummary | None = None


class AuthResponse(TokenPair):
    """Authentication response including the current user."""

    user: UserSummary
