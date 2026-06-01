"""Admin-facing schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.schemas.common import ORMModel


class AccuracyStats(BaseModel):
    """Saved model accuracy metrics."""

    accuracy: float
    precision: float
    recall: float
    f1: float
    roc_auc: float


class ModelStats(BaseModel):
    """Model performance summary."""

    random_forest: AccuracyStats
    xgboost: AccuracyStats
    logistic_regression: AccuracyStats
    ensemble: AccuracyStats


class AuditEntryResponse(ORMModel):
    """Audit log entry shown in the admin console."""

    id: str
    user_id: str
    user_name: str | None = None
    user_email: str | None = None
    action: str
    resource: str
    ip_address: str | None
    timestamp: datetime


class ModelGovernanceResponse(BaseModel):
    """Operational model governance details."""

    environment: str
    artifact_available: bool
    artifact_path: str
    artifact_updated_at: datetime | None
    feature_count: int
    explainer_model_name: str | None


class DoctorDirectoryItem(ORMModel):
    """Doctor listing used for care-team assignment."""

    id: str
    full_name: str
    email: str
    organization_id: str | None
    assigned_patient_count: int


class AdminDoctorCreateRequest(BaseModel):
    """Payload used by admins to create a doctor account."""

    full_name: str = Field(min_length=2, max_length=255)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class AdminDoctorCreateResponse(ORMModel):
    """Newly created doctor account summary."""

    id: str
    full_name: str
    email: EmailStr
    organization_id: str | None
    created_at: datetime


class AdminStatsResponse(BaseModel):
    """Admin dashboard summary payload."""

    active_users: int
    total_doctors: int
    total_patients: int
    total_high_risk_patients: int
    total_predictions_today: int
    total_predictions_week: int
    total_predictions_month: int
    model_version_deployed: str
    model_stats: ModelStats | None
    model_governance: ModelGovernanceResponse
    recent_audit_log: list[AuditEntryResponse]


class ModelDeployResponse(BaseModel):
    """Result returned after a model hot-swap."""

    model_version: str
    model_path: str
    reloaded_at: datetime
