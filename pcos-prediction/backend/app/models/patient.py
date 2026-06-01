"""Patient and laboratory ORM models."""

from __future__ import annotations

import uuid

from sqlalchemy import Float, ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Patient(TimestampMixin, Base):
    """Patient demographic profile."""

    __tablename__ = "patients"

    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    age: Mapped[int | None] = mapped_column(Integer)
    weight: Mapped[float | None] = mapped_column(Float)
    height: Mapped[float | None] = mapped_column(Float)
    bmi: Mapped[float | None] = mapped_column(Float)
    blood_group: Mapped[str | None] = mapped_column(String(24))

    user: Mapped["User"] = relationship("User", back_populates="patient_profile")
    lab_results: Mapped[list["LabResult"]] = relationship(
        "LabResult",
        back_populates="patient",
        cascade="all, delete-orphan",
        order_by="desc(LabResult.created_at)",
    )
    predictions: Mapped[list["Prediction"]] = relationship(
        "Prediction",
        back_populates="patient",
        cascade="all, delete-orphan",
        order_by="desc(Prediction.created_at)",
    )
    assignment: Mapped["PatientAssignment | None"] = relationship(
        "PatientAssignment",
        back_populates="patient",
        uselist=False,
        cascade="all, delete-orphan",
    )
    notes: Mapped[list["ClinicianNote"]] = relationship(
        "ClinicianNote",
        back_populates="patient",
        cascade="all, delete-orphan",
        order_by="desc(ClinicianNote.created_at)",
    )


class LabResult(TimestampMixin, Base):
    """Patient laboratory measurements."""

    __tablename__ = "lab_results"

    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    lh: Mapped[float | None] = mapped_column(Float)
    fsh: Mapped[float | None] = mapped_column(Float)
    lh_fsh_ratio: Mapped[float | None] = mapped_column(Float)
    amh: Mapped[float | None] = mapped_column(Float)
    afc: Mapped[int | None] = mapped_column(Integer)
    tsh: Mapped[float | None] = mapped_column(Float)
    prl: Mapped[float | None] = mapped_column(Float)
    vit_d3: Mapped[float | None] = mapped_column(Float)
    testosterone: Mapped[float | None] = mapped_column(Float)

    patient: Mapped["Patient"] = relationship("Patient", back_populates="lab_results")


from app.models.prediction import Prediction  # noqa: E402
from app.models.assignment import PatientAssignment  # noqa: E402
from app.models.note import ClinicianNote  # noqa: E402
from app.models.user import User  # noqa: E402
