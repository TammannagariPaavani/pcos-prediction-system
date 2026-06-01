"""Prediction ORM model definitions."""

from __future__ import annotations

import uuid

from sqlalchemy import Float, ForeignKey, String, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.models.base import Base, TimestampMixin


json_type = JSON().with_variant(JSONB, "postgresql")


class Prediction(TimestampMixin, Base):
    """Stored PCOS prediction result."""

    __tablename__ = "predictions"

    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    risk_score: Mapped[float] = mapped_column(Float, nullable=False)
    risk_label: Mapped[str] = mapped_column(String(32), nullable=False)
    model_version: Mapped[str] = mapped_column(String(64), nullable=False)
    shap_values: Mapped[list[dict]] = mapped_column(json_type, nullable=False)
    top_features: Mapped[list[dict]] = mapped_column(json_type, nullable=False)

    patient: Mapped["Patient"] = relationship("Patient", back_populates="predictions")


from app.models.patient import Patient  # noqa: E402
