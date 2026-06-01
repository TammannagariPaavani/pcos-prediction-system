"""Clinic workflow services for patients, assignments, drafts, and notes."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session, joinedload

from app.core.dependencies import APIError
from app.models import ClinicianNote, Patient, PatientAssignment, PatientDraft, RoleEnum, User

logger = logging.getLogger(__name__)

def _patient_query_for_user(db: Session, current_user: User):
    """Return the base patient query visible to the current user."""

    query = (
        db.query(Patient)
        .join(Patient.user)
        .options(
            joinedload(Patient.user),
            joinedload(Patient.assignment).joinedload(PatientAssignment.doctor),
            joinedload(Patient.assignment).joinedload(PatientAssignment.assigned_by),
            joinedload(Patient.predictions),
            joinedload(Patient.notes).joinedload(ClinicianNote.author),
        )
    )
    if current_user.role == RoleEnum.doctor:
        query = query.join(Patient.assignment).filter(
            PatientAssignment.doctor_user_id == current_user.id,
            PatientAssignment.is_active.is_(True),
        )
    elif current_user.role == RoleEnum.patient:
        query = query.filter(Patient.user_id == current_user.id)
    return query


def _serialize_assignment(assignment: PatientAssignment | None) -> dict[str, Any] | None:
    """Return a response-ready assignment payload."""

    if assignment is None or assignment.doctor is None:
        return None

    assigned_by = None
    if assignment.assigned_by is not None:
        assigned_by = {
            "id": assignment.assigned_by.id,
            "full_name": assignment.assigned_by.full_name,
            "email": assignment.assigned_by.email,
        }

    return {
        "id": assignment.id,
        "status": assignment.status,
        "is_active": assignment.is_active,
        "created_at": assignment.created_at,
        "doctor": {
            "id": assignment.doctor.id,
            "full_name": assignment.doctor.full_name,
            "email": assignment.doctor.email,
        },
        "assigned_by": assigned_by,
    }


def _serialize_note(note: ClinicianNote) -> dict[str, Any]:
    """Return a response-ready clinician note."""

    return {
        "id": note.id,
        "patient_id": note.patient_id,
        "note_type": note.note_type,
        "note_text": note.note_text,
        "created_at": note.created_at,
        "author": {
            "id": note.author.id,
            "full_name": note.author.full_name,
            "email": note.author.email,
        },
    }


def _serialize_patient(patient: Patient) -> dict[str, Any]:
    """Return a response-ready patient profile."""

    return {
        "id": patient.id,
        "user_id": patient.user_id,
        "age": patient.age,
        "weight": patient.weight,
        "height": patient.height,
        "bmi": patient.bmi,
        "blood_group": patient.blood_group,
        "created_at": patient.created_at,
        "user": {
            "id": patient.user.id,
            "full_name": patient.user.full_name,
            "email": patient.user.email,
        },
        "assignment": _serialize_assignment(patient.assignment),
    }


def get_accessible_patient(db: Session, current_user: User, patient_id: str) -> Patient:
    """Return a patient record only if the user has access to it."""

    patient = _patient_query_for_user(db, current_user).filter(Patient.id == patient_id).one_or_none()
    if patient is None:
        raise APIError("Patient not found or not accessible.", "PATIENT_NOT_FOUND", 404)
    return patient


def list_patients(
    db: Session,
    current_user: User,
    page: int,
    page_size: int,
    risk_label: str | None = None,
    search: str | None = None,
) -> dict[str, Any]:
    """Return a paginated patient list for dashboards."""

    query = _patient_query_for_user(db, current_user)
    if search:
        search_term = f"%{search.strip()}%"
        query = query.filter((User.full_name.ilike(search_term)) | (User.email.ilike(search_term)))

    patients = query.order_by(Patient.created_at.desc()).all()
    items: list[dict[str, Any]] = []
    for patient in patients:
        latest_prediction = patient.predictions[0] if patient.predictions else None
        if risk_label and latest_prediction and latest_prediction.risk_label != risk_label:
            continue
        if risk_label and risk_label != "Unscreened" and latest_prediction is None:
            continue
        if risk_label == "Unscreened" and latest_prediction is not None:
            continue
        items.append(
            {
                "patient_id": patient.id,
                "full_name": patient.user.full_name,
                "email": patient.user.email,
                "age": patient.age,
                "bmi": patient.bmi,
                "latest_risk_label": latest_prediction.risk_label if latest_prediction else None,
                "latest_risk_score": latest_prediction.risk_score if latest_prediction else None,
                "last_prediction_at": latest_prediction.created_at if latest_prediction else None,
                "prediction_count": len(patient.predictions),
                "assigned_doctor_name": patient.assignment.doctor.full_name if patient.assignment else None,
                "assigned_doctor_id": patient.assignment.doctor.id if patient.assignment else None,
            }
        )

    total = len(items)
    start = (page - 1) * page_size
    end = start + page_size
    logger.info(
        "Returning %s patients for %s on page %s.",
        min(page_size, max(total - start, 0)),
        current_user.id,
        page,
    )
    return {
        "page": page,
        "page_size": page_size,
        "total": total,
        "items": items[start:end],
    }


def get_patient_history(db: Session, current_user: User, patient_id: str) -> dict[str, Any]:
    """Return a patient with predictions and clinician notes."""

    patient = get_accessible_patient(db, current_user, patient_id)
    return {
        "patient": _serialize_patient(patient),
        "predictions": patient.predictions,
        "notes": [_serialize_note(note) for note in patient.notes],
    }


def save_patient_draft(db: Session, current_user: User, payload: dict[str, Any], current_step: int) -> PatientDraft:
    """Create or update the authenticated patient's saved draft."""

    draft = db.query(PatientDraft).filter(PatientDraft.user_id == current_user.id).one_or_none()
    if draft is None:
        draft = PatientDraft(user_id=current_user.id)
        db.add(draft)

    draft.draft_payload = payload
    draft.current_step = current_step
    draft.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(draft)
    logger.info("Saved patient draft for user %s at step %s.", current_user.id, current_step)
    return draft


def get_patient_draft(db: Session, current_user: User) -> PatientDraft:
    """Return the saved draft for the authenticated patient."""

    draft = db.query(PatientDraft).filter(PatientDraft.user_id == current_user.id).one_or_none()
    if draft is None:
        raise APIError("No saved draft was found.", "DRAFT_NOT_FOUND", 404)
    return draft


def delete_patient_draft(db: Session, current_user: User) -> None:
    """Delete the saved draft for the authenticated patient."""

    draft = db.query(PatientDraft).filter(PatientDraft.user_id == current_user.id).one_or_none()
    if draft is None:
        return
    db.delete(draft)
    db.commit()
    logger.info("Deleted saved patient draft for user %s.", current_user.id)


def assign_patient_to_doctor(
    db: Session,
    patient_id: str,
    doctor_user_id: str,
    admin_user: User,
) -> PatientAssignment:
    """Assign or reassign a patient to a doctor."""

    patient = db.query(Patient).options(joinedload(Patient.user)).filter(Patient.id == patient_id).one_or_none()
    if patient is None:
        raise APIError("Patient not found.", "PATIENT_NOT_FOUND", 404)

    doctor = db.query(User).filter(User.id == doctor_user_id, User.role == RoleEnum.doctor).one_or_none()
    if doctor is None:
        raise APIError("Doctor not found.", "DOCTOR_NOT_FOUND", 404)
    if admin_user.organization_id and doctor.organization_id != admin_user.organization_id:
        raise APIError("Doctor must belong to your organization.", "INVALID_DOCTOR_ORG", 400)

    assignment = (
        db.query(PatientAssignment)
        .options(joinedload(PatientAssignment.doctor), joinedload(PatientAssignment.assigned_by))
        .filter(PatientAssignment.patient_id == patient.id)
        .one_or_none()
    )
    if assignment is None:
        assignment = PatientAssignment(patient_id=patient.id)
        db.add(assignment)

    assignment.doctor_user_id = doctor.id
    assignment.assigned_by_user_id = admin_user.id
    assignment.status = "active"
    assignment.is_active = True
    db.commit()
    db.refresh(assignment)
    logger.info("Assigned patient %s to doctor %s.", patient.id, doctor.id)
    return assignment


def create_clinician_note(
    db: Session,
    current_user: User,
    patient_id: str,
    note_text: str,
    note_type: str,
) -> ClinicianNote:
    """Store a clinician note for an accessible patient."""

    patient = get_accessible_patient(db, current_user, patient_id)
    note = ClinicianNote(
        patient_id=patient.id,
        author_user_id=current_user.id,
        note_text=note_text.strip(),
        note_type=note_type.strip().lower(),
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    logger.info("Created clinician note %s for patient %s.", note.id, patient.id)
    return (
        db.query(ClinicianNote)
        .options(joinedload(ClinicianNote.author))
        .filter(ClinicianNote.id == note.id)
        .one()
    )


def list_doctors_for_admin(db: Session, current_user: User) -> list[dict[str, Any]]:
    """Return the assignable doctors visible to an admin."""

    query = db.query(User).filter(User.role == RoleEnum.doctor, User.is_active.is_(True))
    if current_user.organization_id:
        query = query.filter(User.organization_id == current_user.organization_id)

    doctors = query.order_by(User.full_name.asc()).all()
    return [
        {
            "id": doctor.id,
            "full_name": doctor.full_name,
            "email": doctor.email,
            "organization_id": doctor.organization_id,
            "assigned_patient_count": len(doctor.assigned_patients),
        }
        for doctor in doctors
    ]
