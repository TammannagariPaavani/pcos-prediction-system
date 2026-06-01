"""Admin endpoints."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile, status
from sqlalchemy import distinct, func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.dependencies import APIError, require_roles, write_audit_log
from app.core.security import hash_password
from app.db.database import get_db
from app.models import AuditLog, Patient, Prediction, RoleEnum, User
from app.schemas import (
    AdminDoctorCreateRequest,
    AdminDoctorCreateResponse,
    AdminStatsResponse,
    DoctorDirectoryItem,
    ModelDeployResponse,
)
from app.services.patient_workflow_service import list_doctors_for_admin
from app.services.prediction_service import reload_model_artifact

router = APIRouter()


def _build_model_governance() -> dict:
    """Return model governance details from the loaded artifact."""

    from app.ml.predict import prediction_engine

    artifact = prediction_engine.artifact or {}
    artifact_path = str(prediction_engine.model_path)
    artifact_updated_at = None
    if prediction_engine.model_path.exists():
        artifact_updated_at = datetime.fromtimestamp(prediction_engine.model_path.stat().st_mtime, tz=timezone.utc)

    return {
        "environment": settings.environment,
        "artifact_available": prediction_engine.is_ready,
        "artifact_path": artifact_path,
        "artifact_updated_at": artifact_updated_at,
        "feature_count": len(artifact.get("feature_columns", [])),
        "explainer_model_name": artifact.get("explainer_model_name"),
    }


@router.get("/stats", response_model=AdminStatsResponse)
def admin_stats(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RoleEnum.admin)),
) -> dict:
    """Return operational metrics and recent audit activity."""

    now = datetime.now(timezone.utc)
    today_cutoff = now - timedelta(days=1)
    week_cutoff = now - timedelta(days=7)
    month_cutoff = now - timedelta(days=30)

    active_users = db.query(func.count(User.id)).filter(User.is_active.is_(True)).scalar() or 0
    total_doctors = db.query(func.count(User.id)).filter(User.role == RoleEnum.doctor).scalar() or 0
    total_patients = db.query(func.count(Patient.id)).scalar() or 0
    total_high_risk_patients = (
        db.query(func.count(distinct(Prediction.patient_id)))
        .filter(Prediction.risk_label == "High")
        .scalar()
        or 0
    )
    total_predictions_today = (
        db.query(func.count(Prediction.id)).filter(Prediction.created_at >= today_cutoff).scalar() or 0
    )
    total_predictions_week = (
        db.query(func.count(Prediction.id)).filter(Prediction.created_at >= week_cutoff).scalar() or 0
    )
    total_predictions_month = (
        db.query(func.count(Prediction.id)).filter(Prediction.created_at >= month_cutoff).scalar() or 0
    )
    recent_audit_log = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(15).all()

    write_audit_log(db, current_user.id, "VIEW_ADMIN_STATS", "admin", request)

    from app.ml.predict import prediction_engine

    model_metrics = prediction_engine.artifact.get("metrics") if prediction_engine.artifact else None
    return {
        "active_users": active_users,
        "total_doctors": total_doctors,
        "total_patients": total_patients,
        "total_high_risk_patients": total_high_risk_patients,
        "total_predictions_today": total_predictions_today,
        "total_predictions_week": total_predictions_week,
        "total_predictions_month": total_predictions_month,
        "model_version_deployed": (
            prediction_engine.artifact["model_version"] if prediction_engine.artifact else settings.model_version
        ),
        "model_stats": model_metrics,
        "model_governance": _build_model_governance(),
        "recent_audit_log": [
            {
                "id": entry.id,
                "user_id": entry.user_id,
                "user_name": entry.user.full_name if entry.user else None,
                "user_email": entry.user.email if entry.user else None,
                "action": entry.action,
                "resource": entry.resource,
                "ip_address": entry.ip_address,
                "timestamp": entry.timestamp,
            }
            for entry in recent_audit_log
        ],
    }


@router.get("/doctors", response_model=list[DoctorDirectoryItem])
def doctor_directory(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RoleEnum.admin)),
) -> list[dict]:
    """Return the admin-visible doctor directory."""

    doctors = list_doctors_for_admin(db, current_user)
    write_audit_log(db, current_user.id, "LIST_DOCTORS", "admin", request)
    return doctors


@router.post("/doctors", response_model=AdminDoctorCreateResponse, status_code=status.HTTP_201_CREATED)
def create_doctor_account(
    payload: AdminDoctorCreateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RoleEnum.admin)),
) -> User:
    """Create a doctor account under the current admin's organization."""

    if current_user.organization_id is None:
        raise APIError(
            "Admin account must belong to an organization before creating doctors.",
            "ADMIN_ORGANIZATION_REQUIRED",
            422,
        )

    existing = db.query(User).filter(User.email == payload.email).one_or_none()
    if existing is not None:
        raise APIError("A user with this email already exists.", "USER_EXISTS", 409)

    doctor = User(
        full_name=payload.full_name.strip(),
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role=RoleEnum.doctor,
        organization_id=current_user.organization_id,
        is_active=True,
    )
    db.add(doctor)
    db.commit()
    db.refresh(doctor)
    write_audit_log(db, current_user.id, "CREATE_DOCTOR", "admin", request)
    return doctor


@router.put("/model/deploy", response_model=ModelDeployResponse)
def deploy_model(
    request: Request,
    model_version: str = Form(...),
    model_file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RoleEnum.admin)),
) -> dict:
    """Hot-swap the active model artifact from an uploaded joblib file."""

    if not model_file.filename.endswith(".joblib"):
        raise APIError("Only .joblib artifacts are supported.", "INVALID_MODEL_FILE", 400)

    target_path = settings.resolved_model_storage_path / f"{model_version}.joblib"
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_bytes(model_file.file.read())
    reload_model_artifact(target_path)
    write_audit_log(db, current_user.id, "DEPLOY_MODEL", "model", request)
    return {
        "model_version": model_version,
        "model_path": str(target_path),
        "reloaded_at": datetime.now(timezone.utc),
    }
