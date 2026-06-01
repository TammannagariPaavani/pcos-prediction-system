"""Create initial PCOS schema."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260402_0001"
down_revision = None
branch_labels = None
depends_on = None


role_enum = sa.Enum("patient", "doctor", "admin", name="role_enum")


def upgrade() -> None:
    """Apply the initial database schema."""

    role_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(as_uuid=False), primary_key=True, nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("role", role_enum, nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=False)
    op.create_index("ix_users_created_at", "users", ["created_at"], unique=False)

    op.create_table(
        "patients",
        sa.Column("id", sa.Uuid(as_uuid=False), primary_key=True, nullable=False),
        sa.Column(
            "user_id",
            sa.Uuid(as_uuid=False),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("age", sa.Integer()),
        sa.Column("weight", sa.Float()),
        sa.Column("height", sa.Float()),
        sa.Column("bmi", sa.Float()),
        sa.Column("blood_group", sa.String(length=24)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_patients_user_id", "patients", ["user_id"], unique=False)
    op.create_index("ix_patients_created_at", "patients", ["created_at"], unique=False)

    op.create_table(
        "lab_results",
        sa.Column("id", sa.Uuid(as_uuid=False), primary_key=True, nullable=False),
        sa.Column(
            "patient_id",
            sa.Uuid(as_uuid=False),
            sa.ForeignKey("patients.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("lh", sa.Float()),
        sa.Column("fsh", sa.Float()),
        sa.Column("lh_fsh_ratio", sa.Float()),
        sa.Column("amh", sa.Float()),
        sa.Column("afc", sa.Integer()),
        sa.Column("tsh", sa.Float()),
        sa.Column("prl", sa.Float()),
        sa.Column("vit_d3", sa.Float()),
        sa.Column("testosterone", sa.Float()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_lab_results_patient_id", "lab_results", ["patient_id"], unique=False)
    op.create_index("ix_lab_results_created_at", "lab_results", ["created_at"], unique=False)

    json_type = postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), "sqlite")
    op.create_table(
        "predictions",
        sa.Column("id", sa.Uuid(as_uuid=False), primary_key=True, nullable=False),
        sa.Column(
            "patient_id",
            sa.Uuid(as_uuid=False),
            sa.ForeignKey("patients.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("risk_score", sa.Float(), nullable=False),
        sa.Column("risk_label", sa.String(length=32), nullable=False),
        sa.Column("model_version", sa.String(length=64), nullable=False),
        sa.Column("shap_values", json_type, nullable=False),
        sa.Column("top_features", json_type, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_predictions_patient_id", "predictions", ["patient_id"], unique=False)
    op.create_index("ix_predictions_created_at", "predictions", ["created_at"], unique=False)

    op.create_table(
        "audit_log",
        sa.Column("id", sa.Uuid(as_uuid=False), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Uuid(as_uuid=False), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("action", sa.String(length=128), nullable=False),
        sa.Column("resource", sa.String(length=128), nullable=False),
        sa.Column("ip_address", sa.String(length=64)),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_audit_log_user_id", "audit_log", ["user_id"], unique=False)
    op.create_index("ix_audit_log_timestamp", "audit_log", ["timestamp"], unique=False)


def downgrade() -> None:
    """Revert the initial database schema."""

    op.drop_index("ix_audit_log_timestamp", table_name="audit_log")
    op.drop_index("ix_audit_log_user_id", table_name="audit_log")
    op.drop_table("audit_log")

    op.drop_index("ix_predictions_created_at", table_name="predictions")
    op.drop_index("ix_predictions_patient_id", table_name="predictions")
    op.drop_table("predictions")

    op.drop_index("ix_lab_results_created_at", table_name="lab_results")
    op.drop_index("ix_lab_results_patient_id", table_name="lab_results")
    op.drop_table("lab_results")

    op.drop_index("ix_patients_created_at", table_name="patients")
    op.drop_index("ix_patients_user_id", table_name="patients")
    op.drop_table("patients")

    op.drop_index("ix_users_created_at", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")

    role_enum.drop(op.get_bind(), checkfirst=True)
