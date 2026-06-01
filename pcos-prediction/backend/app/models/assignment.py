"""Doctor-to-patient assignment ORM models."""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class PatientAssignment(TimestampMixin, Base):
    """Active doctor assignment for a patient."""

    __tablename__ = "patient_assignments"

    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    doctor_user_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    assigned_by_user_id: Mapped[str | None] = mapped_column(
        Uuid(as_uuid=False),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active", server_default="active")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")

    patient: Mapped["Patient"] = relationship("Patient", back_populates="assignment")
    doctor: Mapped["User"] = relationship(
        "User",
        back_populates="assigned_patients",
        foreign_keys=[doctor_user_id],
    )
    assigned_by: Mapped["User | None"] = relationship(
        "User",
        back_populates="created_assignments",
        foreign_keys=[assigned_by_user_id],
    )


from app.models.patient import Patient  # noqa: E402
from app.models.user import User  # noqa: E402
