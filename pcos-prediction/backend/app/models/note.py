"""Clinician note ORM models."""

from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class ClinicianNote(TimestampMixin, Base):
    """Doctor or admin note attached to a patient record."""

    __tablename__ = "clinician_notes"

    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    author_user_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    note_type: Mapped[str] = mapped_column(String(32), nullable=False, default="clinical", server_default="clinical")
    note_text: Mapped[str] = mapped_column(Text, nullable=False)

    patient: Mapped["Patient"] = relationship("Patient", back_populates="notes")
    author: Mapped["User"] = relationship("User", back_populates="authored_notes")


from app.models.patient import Patient  # noqa: E402
from app.models.user import User  # noqa: E402
