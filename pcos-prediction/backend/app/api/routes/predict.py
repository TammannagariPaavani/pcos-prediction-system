"""Prediction endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.dependencies import require_roles
from app.db.database import get_db
from app.models import RoleEnum, User
from app.schemas import PCOSInput, PredictionResponse
from app.services.prediction_service import create_prediction

router = APIRouter()


@router.post("/predict", response_model=PredictionResponse)
def predict_pcos(
    payload: PCOSInput,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RoleEnum.patient)),
) -> dict:
    """Score PCOS risk for the provided clinical profile."""

    return create_prediction(db, current_user, payload.model_dump(), request)
