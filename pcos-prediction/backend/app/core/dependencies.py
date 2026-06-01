"""Dependency helpers, RBAC checks, and audit logging."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Callable

from fastapi import Depends, Request, status
from jose import JWTError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.db.database import get_db
from app.models import AuditLog, RoleEnum, User


logger = logging.getLogger(__name__)


class APIError(Exception):
    """Structured application error."""

    def __init__(self, message: str, code: str, status_code: int) -> None:
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(message)


def error_payload(message: str, code: str) -> dict[str, str]:
    """Return a standardized error payload."""

    return {"error": message, "code": code}


def get_token_from_request(request: Request) -> str:
    """Extract the access token from cookies or the Authorization header."""

    cookie_token = request.cookies.get("access_token")
    if cookie_token:
        return cookie_token

    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        return auth_header.split(" ", maxsplit=1)[1].strip()

    raise APIError(
        "Authentication credentials were not provided.",
        "AUTH_REQUIRED",
        status.HTTP_401_UNAUTHORIZED,
    )


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """Resolve the authenticated user from the access token."""

    token = get_token_from_request(request)
    try:
        payload = decode_token(token)
    except JWTError as exc:
        raise APIError("Invalid or expired token.", "INVALID_TOKEN", status.HTTP_401_UNAUTHORIZED) from exc

    if payload.get("token_type") != "access":
        raise APIError("Invalid token type for this endpoint.", "INVALID_TOKEN_TYPE", status.HTTP_401_UNAUTHORIZED)

    user = db.get(User, payload.get("sub"))
    if user is None:
        raise APIError("User not found.", "USER_NOT_FOUND", status.HTTP_404_NOT_FOUND)
    if not user.is_active:
        raise APIError("Inactive user.", "USER_INACTIVE", status.HTTP_403_FORBIDDEN)
    return user


def require_roles(*roles: RoleEnum) -> Callable[[User], User]:
    """Return a dependency that enforces one of the allowed roles."""

    def _require_role(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise APIError(
                "You do not have permission to access this resource.",
                "FORBIDDEN",
                status.HTTP_403_FORBIDDEN,
            )
        return current_user

    return _require_role


def write_audit_log(db: Session, user_id: str, action: str, resource: str, request: Request | None = None) -> None:
    """Persist an audit trail entry without breaking the main request on SQLite lock issues."""

    ip_address = request.client.host if request and request.client else None
    entry = AuditLog(
        user_id=user_id,
        action=action,
        resource=resource,
        ip_address=ip_address,
        timestamp=datetime.now(timezone.utc),
    )
    try:
        db.add(entry)
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        logger.warning(
            "Skipping audit log write for user_id=%s action=%s resource=%s due to database error: %s",
            user_id,
            action,
            resource,
            exc,
        )


def resolve_patient_scope(current_user: User, patient_user_id: str | None = None) -> str | None:
    """Return the patient scope allowed for the current user."""

    if current_user.role == RoleEnum.patient:
        return current_user.id
    return patient_user_id
