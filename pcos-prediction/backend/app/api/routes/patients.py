"""Patient workflow endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request, Response, status
from sqlalchemy.orm import Session

from app.core.dependencies import APIError, require_roles, write_audit_log
from app.db.database import get_db
from app.models import Patient, RoleEnum, User
from app.schemas import (
    ClinicianNoteCreate,
    ClinicianNoteResponse,
    ErrorResponse,
    PatientAssignmentCreate,
    PatientAssignmentResponse,
    PatientDraftResponse,
    PatientDraftSaveRequest,
    PatientHistoryResponse,
    PatientListResponse,
)
from app.services.patient_workflow_service import (
    assign_patient_to_doctor,
    create_clinician_note,
    delete_patient_draft,
    get_patient_draft,
    get_patient_history,
    list_patients,
    save_patient_draft,
)

router = APIRouter()


@router.get("", response_model=PatientListResponse)
def list_patients_endpoint(
    request: Request,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    risk_label: str | None = Query(default=None),
    search: str | None = Query(default=None, min_length=1, max_length=255),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RoleEnum.doctor, RoleEnum.admin)),
) -> dict:
    """Return the paginated patient list for doctor and admin dashboards."""

    write_audit_log(db, current_user.id, "LIST_PATIENTS", "patient", request)
    return list_patients(db, current_user, page=page, page_size=page_size, risk_label=risk_label, search=search)


@router.get("/me/history", response_model=PatientHistoryResponse)
def patient_my_history(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RoleEnum.patient)),
) -> dict:
    """Return prediction history and doctor notes for the authenticated patient."""

    patient = db.query(Patient).filter(Patient.user_id == current_user.id).one_or_none()
    if patient is None:
        raise APIError("Patient profile not found.", "PATIENT_NOT_FOUND", status.HTTP_404_NOT_FOUND)
    response = get_patient_history(db, current_user, patient.id)
    write_audit_log(db, current_user.id, "VIEW_OWN_HISTORY", "patient", request)
    return response


@router.get("/{patient_id}/history", response_model=PatientHistoryResponse)
def patient_history(
    patient_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RoleEnum.patient, RoleEnum.doctor, RoleEnum.admin)),
) -> dict:
    """Return prediction history and clinician notes for one patient."""

    response = get_patient_history(db, current_user, patient_id)
    write_audit_log(db, current_user.id, "VIEW_HISTORY", "patient", request)
    return response


@router.get("/me/draft", response_model=PatientDraftResponse)
def read_patient_draft(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RoleEnum.patient)),
) -> object:
    """Return the authenticated patient's saved form draft."""

    draft = get_patient_draft(db, current_user)
    write_audit_log(db, current_user.id, "VIEW_DRAFT", "patient_draft", request)
    return draft


@router.put("/me/draft", response_model=PatientDraftResponse)
def upsert_patient_draft(
    payload: PatientDraftSaveRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RoleEnum.patient)),
) -> object:
    """Create or update the authenticated patient's saved draft."""

    draft = save_patient_draft(db, current_user, payload.draft_payload, payload.current_step)
    write_audit_log(db, current_user.id, "SAVE_DRAFT", "patient_draft", request)
    return draft


@router.delete(
    "/me/draft",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={204: {"description": "Draft deleted"}, 401: {"model": ErrorResponse}},
)
def remove_patient_draft(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RoleEnum.patient)),
) -> Response:
    """Delete the authenticated patient's saved draft."""

    delete_patient_draft(db, current_user)
    write_audit_log(db, current_user.id, "DELETE_DRAFT", "patient_draft", request)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/{patient_id}/assignment", response_model=PatientAssignmentResponse)
def update_patient_assignment(
    patient_id: str,
    payload: PatientAssignmentCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RoleEnum.admin)),
) -> object:
    """Assign or reassign a patient to a doctor."""

    assignment = assign_patient_to_doctor(db, patient_id, payload.doctor_user_id, current_user)
    write_audit_log(db, current_user.id, "ASSIGN_PATIENT", "patient_assignment", request)
    return assignment


@router.post("/{patient_id}/notes", response_model=ClinicianNoteResponse, status_code=status.HTTP_201_CREATED)
def create_patient_note(
    patient_id: str,
    payload: ClinicianNoteCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RoleEnum.doctor, RoleEnum.admin)),
) -> object:
    """Create a clinician note for a patient."""

    note = create_clinician_note(db, current_user, patient_id, payload.note_text, payload.note_type)
    write_audit_log(db, current_user.id, "CREATE_NOTE", "clinician_note", request)
    return note
