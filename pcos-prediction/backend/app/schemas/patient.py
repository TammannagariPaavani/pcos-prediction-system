"""Patient and history schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel
from app.schemas.prediction import PredictionRecord


class CareTeamUserSummary(ORMModel):
    """Compact user summary for care-team views."""

    id: str
    full_name: str
    email: str


class PatientAssignmentCreate(BaseModel):
    """Payload used to assign a patient to a doctor."""

    doctor_user_id: str


class PatientAssignmentResponse(ORMModel):
    """Current doctor assignment details."""

    id: str
    status: str
    is_active: bool
    created_at: datetime
    doctor: CareTeamUserSummary
    assigned_by: CareTeamUserSummary | None = None


class ClinicianNoteCreate(BaseModel):
    """Payload used to store a clinician note."""

    note_text: str = Field(min_length=2, max_length=2000)
    note_type: str = Field(default="clinical", min_length=2, max_length=32)


class ClinicianNoteResponse(ORMModel):
    """Persisted clinician note."""

    id: str
    patient_id: str
    note_type: str
    note_text: str
    created_at: datetime
    author: CareTeamUserSummary


class PatientUserSummary(ORMModel):
    """User information nested under a patient profile."""

    id: str
    full_name: str
    email: str


class PatientProfile(ORMModel):
    """Patient profile data."""

    id: str
    user_id: str
    age: int | None
    weight: float | None
    height: float | None
    bmi: float | None
    blood_group: str | None
    created_at: datetime
    user: PatientUserSummary
    assignment: PatientAssignmentResponse | None = None


class PatientHistoryResponse(BaseModel):
    """Prediction history for a patient."""

    patient: PatientProfile
    predictions: list[PredictionRecord]
    notes: list[ClinicianNoteResponse]


class PatientListItem(BaseModel):
    """Doctor-facing patient list item."""

    patient_id: str
    full_name: str
    email: str
    age: int | None
    bmi: float | None
    latest_risk_label: str | None
    latest_risk_score: float | None
    last_prediction_at: datetime | None
    prediction_count: int
    assigned_doctor_name: str | None
    assigned_doctor_id: str | None


class PatientListResponse(BaseModel):
    """Paginated patient list."""

    page: int
    page_size: int
    total: int
    items: list[PatientListItem]


class PatientDraftSaveRequest(BaseModel):
    """Payload used to save an intake draft."""

    draft_payload: dict[str, Any]
    current_step: int = Field(ge=0, le=3)


class PatientDraftResponse(ORMModel):
    """Saved patient intake draft."""

    id: str
    user_id: str
    draft_payload: dict[str, Any]
    current_step: int
    updated_at: datetime
    created_at: datetime
