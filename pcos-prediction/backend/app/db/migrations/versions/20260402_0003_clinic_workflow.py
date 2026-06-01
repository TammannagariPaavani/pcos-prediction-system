"""Add clinic workflow tables for assignments, drafts, and notes."""

from __future__ import annotations

import uuid

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260402_0003"
down_revision = "20260402_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Apply the clinic workflow schema changes."""

    json_type = postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), "sqlite")

    op.create_table(
        "patient_assignments",
        sa.Column("id", sa.Uuid(as_uuid=False), primary_key=True, nullable=False),
        sa.Column(
            "patient_id",
            sa.Uuid(as_uuid=False),
            sa.ForeignKey("patients.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "doctor_user_id",
            sa.Uuid(as_uuid=False),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "assigned_by_user_id",
            sa.Uuid(as_uuid=False),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("patient_id", name="uq_patient_assignments_patient_id"),
    )
    op.create_index("ix_patient_assignments_patient_id", "patient_assignments", ["patient_id"], unique=False)
    op.create_index("ix_patient_assignments_doctor_user_id", "patient_assignments", ["doctor_user_id"], unique=False)
    op.create_index(
        "ix_patient_assignments_assigned_by_user_id",
        "patient_assignments",
        ["assigned_by_user_id"],
        unique=False,
    )
    op.create_index("ix_patient_assignments_created_at", "patient_assignments", ["created_at"], unique=False)

    op.create_table(
        "patient_drafts",
        sa.Column("id", sa.Uuid(as_uuid=False), primary_key=True, nullable=False),
        sa.Column(
            "user_id",
            sa.Uuid(as_uuid=False),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("draft_payload", json_type, nullable=False),
        sa.Column("current_step", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", name="uq_patient_drafts_user_id"),
    )
    op.create_index("ix_patient_drafts_user_id", "patient_drafts", ["user_id"], unique=False)
    op.create_index("ix_patient_drafts_created_at", "patient_drafts", ["created_at"], unique=False)

    op.create_table(
        "clinician_notes",
        sa.Column("id", sa.Uuid(as_uuid=False), primary_key=True, nullable=False),
        sa.Column(
            "patient_id",
            sa.Uuid(as_uuid=False),
            sa.ForeignKey("patients.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "author_user_id",
            sa.Uuid(as_uuid=False),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("note_type", sa.String(length=32), nullable=False, server_default="clinical"),
        sa.Column("note_text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_clinician_notes_patient_id", "clinician_notes", ["patient_id"], unique=False)
    op.create_index("ix_clinician_notes_author_user_id", "clinician_notes", ["author_user_id"], unique=False)
    op.create_index("ix_clinician_notes_created_at", "clinician_notes", ["created_at"], unique=False)

    connection = op.get_bind()
    patient_users = connection.execute(sa.text("SELECT id FROM users WHERE role = 'patient'")).fetchall()
    existing_patient_user_ids = {
        row[0] for row in connection.execute(sa.text("SELECT user_id FROM patients")).fetchall()
    }
    for (user_id,) in patient_users:
        if user_id not in existing_patient_user_ids:
            connection.execute(
                sa.text(
                    """
                    INSERT INTO patients (id, user_id, created_at)
                    VALUES (:id, :user_id, CURRENT_TIMESTAMP)
                    """
                ),
                {"id": str(uuid.uuid4()), "user_id": user_id},
            )


def downgrade() -> None:
    """Revert the clinic workflow schema changes."""

    op.drop_index("ix_clinician_notes_created_at", table_name="clinician_notes")
    op.drop_index("ix_clinician_notes_author_user_id", table_name="clinician_notes")
    op.drop_index("ix_clinician_notes_patient_id", table_name="clinician_notes")
    op.drop_table("clinician_notes")

    op.drop_index("ix_patient_drafts_created_at", table_name="patient_drafts")
    op.drop_index("ix_patient_drafts_user_id", table_name="patient_drafts")
    op.drop_table("patient_drafts")

    op.drop_index("ix_patient_assignments_created_at", table_name="patient_assignments")
    op.drop_index("ix_patient_assignments_assigned_by_user_id", table_name="patient_assignments")
    op.drop_index("ix_patient_assignments_doctor_user_id", table_name="patient_assignments")
    op.drop_index("ix_patient_assignments_patient_id", table_name="patient_assignments")
    op.drop_table("patient_assignments")
