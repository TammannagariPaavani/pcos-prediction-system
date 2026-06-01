"""Prediction report endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.dependencies import APIError, require_roles, write_audit_log
from app.db.database import get_db
from app.models import Prediction, RoleEnum, User
from app.schemas import PredictionReportResponse
from app.services.report_service import store_report

router = APIRouter()


@router.get("/{prediction_id}", response_model=PredictionReportResponse)
def generate_report(
    prediction_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RoleEnum.patient, RoleEnum.doctor, RoleEnum.admin)),
) -> dict[str, str]:
    """Generate and return a PDF report URL for a prediction."""

    prediction = db.get(Prediction, prediction_id)
    if prediction is None:
        raise APIError("Prediction not found.", "PREDICTION_NOT_FOUND", 404)
    patient = prediction.patient
    if current_user.role == RoleEnum.patient and patient.user_id != current_user.id:
        raise APIError("You can only access your own reports.", "FORBIDDEN", 403)

    result = store_report(prediction, patient, str(request.base_url))
    write_audit_log(db, current_user.id, "GENERATE_REPORT", "report", request)
    return result
