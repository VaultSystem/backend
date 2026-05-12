"""Initial vault schema.

Revision ID: 20260512_0001
Revises:
Create Date: 2026-05-12
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260512_0001"
down_revision = None
branch_labels = None
depends_on = None


def timestamp_column(name: str) -> sa.Column:
    return sa.Column(
        name,
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        nullable=False,
    )


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("first_name", sa.String(length=80), nullable=False),
        sa.Column("last_name", sa.String(length=80), nullable=True),
        sa.Column("password_hash", sa.String(length=500), nullable=False),
        sa.Column("last_login", sa.DateTime(timezone=True), nullable=True),
        timestamp_column("created_at"),
        timestamp_column("updated_at"),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("email_verified", sa.Boolean(), nullable=False),
        sa.Column("mfa_enabled", sa.Boolean(), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    op.create_table(
        "roles",
        sa.Column("name", sa.String(length=30), nullable=False),
        timestamp_column("created_at"),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    op.create_table(
        "permissions",
        sa.Column("name", sa.String(length=30), nullable=False),
        timestamp_column("created_at"),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    op.create_table(
        "secrets",
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("owner_id", sa.Integer(), nullable=False),
        sa.Column("current_version_id", sa.Integer(), nullable=True),
        timestamp_column("created_at"),
        timestamp_column("updated_at"),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("owner_id", "name", name="uq_secrets_owner_name"),
    )
    op.create_index(op.f("ix_secrets_name"), "secrets", ["name"], unique=False)

    op.create_table(
        "secret_versions",
        sa.Column("secret_id", sa.Integer(), nullable=False),
        sa.Column("encrypted_value", sa.Text(), nullable=False),
        sa.Column("encrypted_data_key", sa.Text(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        timestamp_column("created_at"),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["secret_id"], ["secrets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("secret_id", "version", name="uq_secret_versions_secret_version"),
    )
    op.create_index(
        op.f("ix_secret_versions_secret_id"),
        "secret_versions",
        ["secret_id"],
        unique=False,
    )
    op.create_foreign_key(
        "fk_secrets_current_version_id_secret_versions",
        "secrets",
        "secret_versions",
        ["current_version_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.create_table(
        "role_permissions",
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.Column("permission_id", sa.Integer(), nullable=False),
        timestamp_column("created_at"),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["permission_id"], ["permissions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("role_id", "permission_id", name="uq_role_permissions_role_permission"),
    )

    op.create_table(
        "access_policies",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("secret_id", sa.Integer(), nullable=False),
        sa.Column("role_id", sa.Integer(), nullable=False),
        timestamp_column("created_at"),
        timestamp_column("updated_at"),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["secret_id"], ["secrets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "secret_id", name="uq_access_policies_user_secret"),
    )

    op.create_table(
        "audit_logs",
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("secret_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(length=80), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        timestamp_column("timestamp"),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["secret_id"], ["secrets.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_audit_logs_action"), "audit_logs", ["action"], unique=False)
    op.create_index(op.f("ix_audit_logs_secret_id"), "audit_logs", ["secret_id"], unique=False)
    op.create_index(op.f("ix_audit_logs_user_id"), "audit_logs", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_audit_logs_user_id"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_secret_id"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_action"), table_name="audit_logs")
    op.drop_table("audit_logs")
    op.drop_table("access_policies")
    op.drop_table("role_permissions")
    op.drop_constraint(
        "fk_secrets_current_version_id_secret_versions",
        "secrets",
        type_="foreignkey",
    )
    op.drop_index(op.f("ix_secret_versions_secret_id"), table_name="secret_versions")
    op.drop_table("secret_versions")
    op.drop_index(op.f("ix_secrets_name"), table_name="secrets")
    op.drop_table("secrets")
    op.drop_table("permissions")
    op.drop_table("roles")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
