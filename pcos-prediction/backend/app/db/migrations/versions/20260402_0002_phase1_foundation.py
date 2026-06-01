"""Add organizations and user profile fields."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260402_0002"
down_revision = "20260402_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Apply the phase 1 foundation schema changes."""

    op.create_table(
        "organizations",
        sa.Column("id", sa.Uuid(as_uuid=False), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("name", name="uq_organizations_name"),
        sa.UniqueConstraint("slug", name="uq_organizations_slug"),
    )
    op.create_index("ix_organizations_slug", "organizations", ["slug"], unique=False)
    op.create_index("ix_organizations_created_at", "organizations", ["created_at"], unique=False)

    op.add_column("users", sa.Column("full_name", sa.String(length=255), nullable=True))
    op.add_column("users", sa.Column("organization_id", sa.Uuid(as_uuid=False), nullable=True))
    op.create_index("ix_users_organization_id", "users", ["organization_id"], unique=False)
    op.create_foreign_key(
        "fk_users_organization_id_organizations",
        "users",
        "organizations",
        ["organization_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.execute("UPDATE users SET full_name = email WHERE full_name IS NULL")
    op.alter_column("users", "full_name", nullable=False)


def downgrade() -> None:
    """Revert the phase 1 foundation schema changes."""

    op.drop_constraint("fk_users_organization_id_organizations", "users", type_="foreignkey")
    op.drop_index("ix_users_organization_id", table_name="users")
    op.drop_column("users", "organization_id")
    op.drop_column("users", "full_name")

    op.drop_index("ix_organizations_created_at", table_name="organizations")
    op.drop_index("ix_organizations_slug", table_name="organizations")
    op.drop_table("organizations")
