"""User ORM model definitions."""

from __future__ import annotations

import enum
import uuid

from sqlalchemy import Boolean, Enum, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class RoleEnum(str, enum.Enum):
    """Supported RBAC roles."""

    patient = "patient"
    doctor = "doctor"
    admin = "admin"


class User(TimestampMixin, Base):
    """Application user account."""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[RoleEnum] = mapped_column(Enum(RoleEnum, name="role_enum"), nullable=False)
    organization_id: Mapped[str | None] = mapped_column(
        Uuid(as_uuid=False),
        ForeignKey("organizations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")

    organization: Mapped["Organization | None"] = relationship("Organization", back_populates="users")
    patient_profile: Mapped["Patient | None"] = relationship("Patient", back_populates="user", uselist=False)
    audit_entries: Mapped[list["AuditLog"]] = relationship("AuditLog", back_populates="user")
    draft: Mapped["PatientDraft | None"] = relationship(
        "PatientDraft",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    assigned_patients: Mapped[list["PatientAssignment"]] = relationship(
        "PatientAssignment",
        back_populates="doctor",
        foreign_keys="PatientAssignment.doctor_user_id",
    )
    created_assignments: Mapped[list["PatientAssignment"]] = relationship(
        "PatientAssignment",
        back_populates="assigned_by",
        foreign_keys="PatientAssignment.assigned_by_user_id",
    )
    authored_notes: Mapped[list["ClinicianNote"]] = relationship("ClinicianNote", back_populates="author")


from app.models.audit import AuditLog  # noqa: E402
from app.models.assignment import PatientAssignment  # noqa: E402
from app.models.draft import PatientDraft  # noqa: E402
from app.models.note import ClinicianNote  # noqa: E402
from app.models.organization import Organization  # noqa: E402
from app.models.patient import Patient  # noqa: E402
