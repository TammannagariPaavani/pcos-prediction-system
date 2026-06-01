"""Prediction service layer."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from fastapi import Request
from sqlalchemy.orm import Session

from app.core.celery_app import celery_app
from app.core.dependencies import APIError, write_audit_log
from app.ml.features import DISPLAY_NAME_MAP, testosterone_proxy
from app.ml.predict import prediction_engine
from app.models import LabResult, Patient, PatientDraft, Prediction, RoleEnum, User
from app.services.notification_service import send_prediction_notification

logger = logging.getLogger(__name__)


OPTIONAL_CLINICAL_FIELDS = [
    "fsh",
    "lh",
    "hip",
    "waist",
    "tsh",
    "amh",
    "prl",
    "vit_d3",
    "prg",
    "rbs",
    "bp_systolic",
    "bp_diastolic",
    "follicle_l",
    "follicle_r",
    "avg_f_size_l",
    "avg_f_size_r",
    "afc",
    "endometrium",
]


def _risk_band(score: float) -> tuple[str, str, str]:
    """Map a risk score to its label, color, and recommendation."""

    if score >= 0.65:
        return (
            "High",
            "#E24B4A",
            "High likelihood of PCOS. Consult an endocrinologist. Consider hormonal panel and pelvic ultrasound.",
        )
    if score >= 0.35:
        return (
            "Medium",
            "#F59E0B",
            "Moderate likelihood of PCOS. Prioritize follow-up testing, nutrition review, and a gynecology consult.",
        )
    return (
        "Low",
        "#10B981",
        "Low likelihood of PCOS. Maintain healthy habits and continue routine reproductive health screening.",
    )


def _upsert_patient_profile(db: Session, user: User, payload: dict[str, Any]) -> Patient:
    """Create or update the patient profile linked to the current user."""

    patient = db.query(Patient).filter(Patient.user_id == user.id).one_or_none()
    if patient is None:
        patient = Patient(user_id=user.id)
        db.add(patient)

    patient.age = payload["age"]
    patient.weight = payload["weight"]
    patient.height = payload["height"]
    patient.bmi = payload["bmi"]
    patient.blood_group = payload["blood_group"]
    db.flush()
    return patient


def _store_lab_results(db: Session, patient: Patient, payload: dict[str, Any]) -> LabResult | None:
    """Persist the lab summary for the prediction request."""

    if all(payload.get(field) is None for field in OPTIONAL_CLINICAL_FIELDS):
        return None

    lab_result = LabResult(
        patient_id=patient.id,
        lh=payload["lh"],
        fsh=payload["fsh"],
        lh_fsh_ratio=(payload["lh"] / payload["fsh"]) if payload["fsh"] else 0.0,
        amh=payload["amh"],
        afc=payload["afc"],
        tsh=payload["tsh"],
        prl=payload["prl"],
        vit_d3=payload["vit_d3"],
        testosterone=testosterone_proxy(
            {
                "hair_growth": payload["hair_growth"],
                "pimples": payload["pimples"],
                "hair_loss": payload["hair_loss"],
                "skin_darkening": payload["skin_darkening"],
                "weight_gain": payload["weight_gain"],
            }
        ),
    )
    db.add(lab_result)
    db.flush()
    return lab_result


def _summarize_clinical_data(payload: dict[str, Any]) -> tuple[str, str, list[str]]:
    """Describe how much clinician-entered data is available for this prediction."""

    missing_fields = [
        DISPLAY_NAME_MAP.get(field_name, field_name)
        for field_name in OPTIONAL_CLINICAL_FIELDS
        if payload.get(field_name) is None
    ]
    provided_count = len(OPTIONAL_CLINICAL_FIELDS) - len(missing_fields)

    if provided_count == 0:
        return ("Patient Screening", "self_reported_only", missing_fields)
    if not missing_fields:
        return ("Clinical Assessment", "complete", [])
    return ("Hybrid Assessment", "partial", missing_fields)


def _recommendation_for_context(
    risk_score: float,
    clinical_data_status: str,
) -> tuple[str, str, str]:
    """Return a recommendation adjusted for the available data depth."""

    risk_label, risk_color, recommendation = _risk_band(risk_score)
    if clinical_data_status == "self_reported_only":
        recommendation = (
            f"{recommendation} This screening is based on self-reported information. "
            "A doctor should confirm hormones and ultrasound findings before clinical decisions are made."
        )
    elif clinical_data_status == "partial":
        recommendation = (
            f"{recommendation} Some clinical values are still missing, so doctor review and remaining lab work are recommended."
        )
    return risk_label, risk_color, recommendation


def create_prediction(db: Session, user: User, payload: dict[str, Any], request: Request) -> dict[str, Any]:
    """Run a model inference, persist all supporting records, and return the API payload."""

    if not prediction_engine.is_ready:
        raise APIError("The model artifact is not available.", "MODEL_OFFLINE", 503)

    assessment_type, clinical_data_status, missing_clinical_fields = _summarize_clinical_data(payload)
    patient = _upsert_patient_profile(db, user, payload)
    _store_lab_results(db, patient, payload)

    prediction_result = prediction_engine.predict(payload)
    risk_label, risk_color, recommendation = _recommendation_for_context(
        prediction_result["risk_score"],
        clinical_data_status,
    )

    prediction = Prediction(
        patient_id=patient.id,
        risk_score=prediction_result["risk_score"],
        risk_label=risk_label,
        model_version=prediction_result["model_version"],
        shap_values=prediction_result["top_features"],
        top_features=prediction_result["top_features"],
    )
    db.add(prediction)
    db.commit()
    db.refresh(prediction)

    saved_draft = db.query(PatientDraft).filter(PatientDraft.user_id == user.id).one_or_none()
    if saved_draft is not None:
        db.delete(saved_draft)
        db.commit()

    write_audit_log(db, user.id, "PREDICT", "prediction", request)
    send_prediction_notification(user.email, f"PCOS risk assessment completed with {risk_label.lower()} risk.")

    return {
        "risk_score": round(prediction.risk_score, 4),
        "risk_label": risk_label,
        "risk_color": risk_color,
        "assessment_type": assessment_type,
        "clinical_data_status": clinical_data_status,
        "missing_clinical_fields": missing_clinical_fields,
        "top_features": prediction_result["top_features"][:5],
        "recommendation": recommendation,
        "model_version": prediction.model_version,
        "prediction_id": prediction.id,
    }


def get_patient_history(db: Session, patient_id: str) -> Patient:
    """Return a patient with prediction history or raise an API error."""

    patient = db.query(Patient).filter(Patient.id == patient_id).one_or_none()
    if patient is None:
        raise APIError("Patient not found.", "PATIENT_NOT_FOUND", 404)
    return patient


def list_patients_for_dashboard(db: Session, current_user: User) -> list[dict[str, Any]]:
    """Return the doctor dashboard list of patients."""

    query = db.query(Patient)
    if current_user.role == RoleEnum.doctor and current_user.organization_id:
        query = query.join(Patient.user).filter(User.organization_id == current_user.organization_id)
    patients = query.order_by(Patient.created_at.desc()).all()
    items: list[dict[str, Any]] = []
    for patient in patients:
        latest_prediction = patient.predictions[0] if patient.predictions else None
        items.append(
            {
                "patient_id": patient.id,
                "email": patient.user.email,
                "age": patient.age,
                "bmi": patient.bmi,
                "latest_risk_label": latest_prediction.risk_label if latest_prediction else None,
                "latest_risk_score": latest_prediction.risk_score if latest_prediction else None,
                "last_prediction_at": latest_prediction.created_at if latest_prediction else None,
            }
        )
    return items


def reload_model_artifact(model_path: str | Path) -> None:
    """Reload the active ensemble artifact from disk."""

    prediction_engine.reload(model_path)
    logger.info("Reloaded model artifact from %s", model_path)


@celery_app.task(name="pcos_prediction.run_prediction")
def run_prediction_job(payload: dict[str, Any]) -> dict[str, Any]:
    """Celery task wrapper for async prediction execution."""

    if not prediction_engine.is_ready:
        raise RuntimeError("Model artifact is not available for async prediction.")
    return prediction_engine.predict(payload)
