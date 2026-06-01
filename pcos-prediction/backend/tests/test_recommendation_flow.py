"""Doctor-to-patient recommendation flow tests."""

from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from app.core.security import hash_password
from app.db.database import SessionLocal
from app.main import app
from app.models import Patient, PatientAssignment, RoleEnum, User


def test_doctor_recommended_tests_show_in_patient_history():
    """Recommended tests saved by a doctor should be visible in the patient's own portal history."""

    suffix = uuid.uuid4().hex[:8]

    patient_client = TestClient(app)
    register_response = patient_client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Portal Patient",
            "email": f"portal-patient-{suffix}@example.com",
            "password": "StrongPass123",
            "role": "patient",
        },
    )
    assert register_response.status_code == 201

    session = SessionLocal()
    doctor = User(
        full_name="Clinic Doctor",
        email=f"clinic-doctor-{suffix}@example.com",
        hashed_password=hash_password("StrongPass123"),
        role=RoleEnum.doctor,
        is_active=True,
    )
    session.add(doctor)
    session.commit()

    patient = (
        session.query(Patient)
        .join(Patient.user)
        .filter(User.email == f"portal-patient-{suffix}@example.com")
        .one()
    )
    assignment = PatientAssignment(
        patient_id=patient.id,
        doctor_user_id=doctor.id,
        assigned_by_user_id=doctor.id,
        status="active",
        is_active=True,
    )
    session.add(assignment)
    session.commit()
    patient_id = patient.id
    session.close()

    doctor_client = TestClient(app)
    doctor_login = doctor_client.post(
        "/api/v1/auth/login",
        json={
            "email": f"clinic-doctor-{suffix}@example.com",
            "password": "StrongPass123",
        },
    )
    assert doctor_login.status_code == 200

    recommendation_response = doctor_client.post(
        f"/api/v1/patients/{patient_id}/notes",
        json={
          "note_text": "Recommended tests:\n- Hormone testing\n- Pelvic ultrasound",
          "note_type": "recommended_tests",
        },
    )
    assert recommendation_response.status_code == 201

    patient_login = patient_client.post(
        "/api/v1/auth/login",
        json={
            "email": f"portal-patient-{suffix}@example.com",
            "password": "StrongPass123",
        },
    )
    assert patient_login.status_code == 200

    history_response = patient_client.get("/api/v1/patients/me/history")
    assert history_response.status_code == 200
    payload = history_response.json()
    recommended_notes = [note for note in payload["notes"] if note["note_type"] == "recommended_tests"]

    assert len(recommended_notes) == 1
    assert "Hormone testing" in recommended_notes[0]["note_text"]
    assert "Pelvic ultrasound" in recommended_notes[0]["note_text"]
