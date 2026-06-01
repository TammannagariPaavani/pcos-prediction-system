"""Prediction request and response schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class PCOSInput(BaseModel):
    """Validated request body for PCOS risk prediction."""

    age: int = Field(ge=10, le=60)
    weight: float = Field(ge=20, le=200)
    height: float = Field(ge=100, le=220)
    bmi: float = Field(ge=10, le=60)
    blood_group: str
    cycle_regularity: int = Field(ge=0, le=1)
    cycle_length: int = Field(ge=20, le=90)
    marriage_years: int = Field(ge=0, le=50)
    pregnant: int = Field(ge=0, le=1)
    abortions: int = Field(ge=0, le=10)
    fsh: float | None = Field(default=None)
    lh: float | None = Field(default=None)
    hip: float | None = Field(default=None)
    waist: float | None = Field(default=None)
    tsh: float | None = Field(default=None)
    amh: float | None = Field(default=None)
    prl: float | None = Field(default=None)
    vit_d3: float | None = Field(default=None)
    prg: float | None = Field(default=None)
    rbs: float | None = Field(default=None)
    weight_gain: int = Field(ge=0, le=1)
    hair_growth: int = Field(ge=0, le=1)
    skin_darkening: int = Field(ge=0, le=1)
    hair_loss: int = Field(ge=0, le=1)
    pimples: int = Field(ge=0, le=1)
    fast_food: int = Field(ge=0, le=1)
    exercise: int = Field(ge=0, le=1)
    bp_systolic: int | None = Field(default=None)
    bp_diastolic: int | None = Field(default=None)
    follicle_l: int | None = Field(default=None)
    follicle_r: int | None = Field(default=None)
    avg_f_size_l: float | None = Field(default=None)
    avg_f_size_r: float | None = Field(default=None)
    afc: int | None = Field(default=None)
    endometrium: float | None = Field(default=None)


class FeatureImpact(BaseModel):
    """Single SHAP feature contribution entry."""

    feature: str
    impact: float
    value: float


class PredictionResponse(BaseModel):
    """Prediction output returned by the API."""

    risk_score: float
    risk_label: str
    risk_color: str
    assessment_type: str
    clinical_data_status: str
    missing_clinical_fields: list[str]
    top_features: list[FeatureImpact]
    recommendation: str
    model_version: str
    prediction_id: str


class PredictionRecord(ORMModel):
    """Persisted prediction response used in history endpoints."""

    id: str
    patient_id: str
    risk_score: float
    risk_label: str
    model_version: str
    shap_values: list[dict]
    top_features: list[dict]
    created_at: datetime


class PredictionReportResponse(BaseModel):
    """Generated PDF report descriptor."""

    prediction_id: str
    download_url: str
    object_key: str
