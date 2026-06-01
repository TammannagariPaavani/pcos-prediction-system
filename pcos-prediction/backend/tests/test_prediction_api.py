"""Prediction API integration tests."""

from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from app.core.security import hash_password
from app.db.database import SessionLocal
from app.main import app
from app.models import RoleEnum, User


def test_patient_screening_allows_missing_optional_clinical_fields():
    """Patients should be able to submit a screening without lab and scan values."""

    suffix = uuid.uuid4().hex[:8]
    session = SessionLocal()
    user = User(
        full_name="Patient Screening User",
        email=f"patient-screening-{suffix}@example.com",
        hashed_password=hash_password("StrongPass123"),
        role=RoleEnum.patient,
        is_active=True,
    )
    session.add(user)
    session.commit()
    session.close()

    client = TestClient(app)
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": f"patient-screening-{suffix}@example.com",
            "password": "StrongPass123",
        },
    )
    assert login_response.status_code == 200

    prediction_response = client.post(
        "/api/v1/predict",
        json={
            "age": 25,
            "weight": 60,
            "height": 160,
            "bmi": 23.4,
            "blood_group": "O+",
            "cycle_regularity": 0,
            "cycle_length": 40,
            "marriage_years": 0,
            "pregnant": 0,
            "abortions": 0,
            "weight_gain": 1,
            "hair_growth": 1,
            "skin_darkening": 0,
            "hair_loss": 0,
            "pimples": 1,
            "fast_food": 1,
            "exercise": 0,
        },
    )

    assert prediction_response.status_code == 200
    payload = prediction_response.json()
    assert payload["assessment_type"] == "Patient Screening"
    assert payload["clinical_data_status"] == "self_reported_only"
    assert "FSH" in payload["missing_clinical_fields"]
