"""Admin workflow integration tests."""

from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from app.core.security import hash_password
from app.db.database import SessionLocal
from app.main import app
from app.models import Organization, RoleEnum, User


def test_public_signup_rejects_doctor_accounts():
    """Public registration should stay limited to patient accounts."""

    client = TestClient(app)
    suffix = uuid.uuid4().hex[:8]

    response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Public Doctor",
            "email": f"public-doctor-{suffix}@example.com",
            "password": "StrongPass123",
            "role": "doctor",
            "organization_name": "Clinic One",
        },
    )

    assert response.status_code == 403
    assert response.json()["code"] == "PUBLIC_SIGNUP_PATIENT_ONLY"


def test_admin_can_create_doctor_and_see_updated_dashboard_counts():
    """Admin users should be able to create doctors and see updated summary metrics."""

    client = TestClient(app)
    suffix = uuid.uuid4().hex[:8]
    session = SessionLocal()

    organization = Organization(name=f"City Care Clinic {suffix}", slug=f"city-care-clinic-{suffix}")
    session.add(organization)
    session.flush()

    admin_user = User(
        full_name="Clinic Admin",
        email=f"admin-{suffix}@example.com",
        hashed_password=hash_password("StrongPass123"),
        role=RoleEnum.admin,
        organization_id=organization.id,
        is_active=True,
    )
    session.add(admin_user)
    session.commit()
    session.close()

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": f"admin-{suffix}@example.com",
            "password": "StrongPass123",
        },
    )
    assert login_response.status_code == 200

    create_doctor_response = client.post(
        "/api/v1/admin/doctors",
        json={
            "full_name": "Dr. Priya Shah",
            "email": f"doctor-{suffix}@example.com",
            "password": "StrongPass123",
        },
    )
    assert create_doctor_response.status_code == 201
    created_doctor = create_doctor_response.json()
    assert created_doctor["full_name"] == "Dr. Priya Shah"
    assert created_doctor["email"] == f"doctor-{suffix}@example.com"

    stats_response = client.get("/api/v1/admin/stats")
    assert stats_response.status_code == 200
    stats_payload = stats_response.json()
    assert stats_payload["total_doctors"] >= 1
    assert stats_payload["total_patients"] >= 0
    assert stats_payload["total_high_risk_patients"] >= 0

    doctors_response = client.get("/api/v1/admin/doctors")
    assert doctors_response.status_code == 200
    doctor_emails = [doctor["email"] for doctor in doctors_response.json()]
    assert f"doctor-{suffix}@example.com" in doctor_emails
