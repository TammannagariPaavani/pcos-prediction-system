"""Authentication endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session

from app.core.dependencies import APIError, get_current_user, write_audit_log
from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_cookie_max_age,
    hash_password,
    verify_password,
)
from app.db.database import get_db
from app.models import Patient, RoleEnum, User
from app.schemas import AuthResponse, UserCreate, UserLogin, UserSummary
from app.services.organization_service import get_or_create_organization, require_organization_name

router = APIRouter()


def _set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    """Attach secure auth cookies to the response."""

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        samesite="lax",
        secure=settings.cookie_secure,
        max_age=get_cookie_max_age("access"),
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        samesite="lax",
        secure=settings.cookie_secure,
        max_age=get_cookie_max_age("refresh"),
    )


@router.post("/register", response_model=UserSummary, status_code=status.HTTP_201_CREATED)
def register_user(payload: UserCreate, request: Request, db: Session = Depends(get_db)) -> User:
    """Register a patient account through the public signup flow."""

    existing = db.query(User).filter(User.email == payload.email).one_or_none()
    if existing is not None:
        raise APIError("A user with this email already exists.", "USER_EXISTS", status.HTTP_409_CONFLICT)

    if payload.role != RoleEnum.patient:
        raise APIError(
            "Public signup is available for patient accounts only.",
            "PUBLIC_SIGNUP_PATIENT_ONLY",
            status.HTTP_403_FORBIDDEN,
        )

    require_organization_name(payload.role.value, payload.organization_name)
    organization = None
    if payload.organization_name:
        organization = get_or_create_organization(db, payload.organization_name)

    user = User(
        full_name=payload.full_name.strip(),
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role=payload.role,
        organization=organization,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    if user.role == RoleEnum.patient and user.patient_profile is None:
        db.add(Patient(user_id=user.id))
        db.commit()
        db.refresh(user)

    write_audit_log(db, user.id, "REGISTER", "user", request)
    return user


@router.post("/login", response_model=AuthResponse)
def login_user(payload: UserLogin, response: Response, request: Request, db: Session = Depends(get_db)) -> dict:
    """Authenticate a user and issue JWT cookies."""

    user = db.query(User).filter(User.email == payload.email).one_or_none()
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise APIError("Incorrect email or password.", "INVALID_CREDENTIALS", status.HTTP_401_UNAUTHORIZED)
    if not user.is_active:
        raise APIError("This account is inactive.", "USER_INACTIVE", status.HTTP_403_FORBIDDEN)

    access_token = create_access_token(user.id, user.role)
    refresh_token = create_refresh_token(user.id, user.role)
    _set_auth_cookies(response, access_token, refresh_token)
    write_audit_log(db, user.id, "LOGIN", "auth", request)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user,
    }


@router.post("/refresh", response_model=AuthResponse)
def refresh_access_token(response: Response, request: Request, db: Session = Depends(get_db)) -> dict:
    """Issue fresh access and refresh tokens from the refresh cookie."""

    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise APIError("Refresh token cookie is missing.", "REFRESH_TOKEN_MISSING", status.HTTP_401_UNAUTHORIZED)

    try:
        payload = decode_token(refresh_token)
    except Exception as exc:
        raise APIError("Invalid refresh token.", "INVALID_REFRESH_TOKEN", status.HTTP_401_UNAUTHORIZED) from exc

    if payload.get("token_type") != "refresh":
        raise APIError("Refresh token is invalid.", "INVALID_REFRESH_TOKEN", status.HTTP_401_UNAUTHORIZED)

    user = db.get(User, payload.get("sub"))
    if user is None:
        raise APIError("User not found.", "USER_NOT_FOUND", status.HTTP_404_NOT_FOUND)

    access_token = create_access_token(user.id, user.role)
    new_refresh_token = create_refresh_token(user.id, user.role)
    _set_auth_cookies(response, access_token, new_refresh_token)
    write_audit_log(db, user.id, "REFRESH_TOKEN", "auth", request)
    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
        "user": user,
    }


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout_user() -> Response:
    """Clear the auth cookies."""

    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    response.delete_cookie("access_token", path="/", secure=settings.cookie_secure, samesite="lax")
    response.delete_cookie("refresh_token", path="/", secure=settings.cookie_secure, samesite="lax")
    return response


@router.get("/me", response_model=UserSummary)
def read_current_user(current_user: User = Depends(get_current_user)) -> User:
    """Return the authenticated user."""

    return current_user
