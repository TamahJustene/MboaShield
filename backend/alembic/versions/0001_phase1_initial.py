"""Phase 1 initial schema — users, checks, incidents, audit, refresh tokens.

Revision ID: 0001_phase1
Revises:
Create Date: 2026-07-16
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0001_phase1"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("role", sa.String(length=64), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=True),
        sa.Column("failed_login_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("locked_until", sa.String(length=64), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "institutions",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("short_name", sa.String(length=128), nullable=False),
        sa.Column("website_url", sa.String(length=512), nullable=True),
        sa.Column("verified", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("handles_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "verification_checks",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("check_type", sa.String(length=64), nullable=False),
        sa.Column("input_text", sa.Text(), nullable=True),
        sa.Column("input_handle", sa.String(length=255), nullable=True),
        sa.Column("input_filename", sa.String(length=512), nullable=True),
        sa.Column("input_lang", sa.String(length=16), nullable=False),
        sa.Column("risk_score", sa.Integer(), nullable=True),
        sa.Column("risk_band", sa.String(length=32), nullable=True),
        sa.Column("result_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_verification_checks_check_type", "verification_checks", ["check_type"])

    op.create_table(
        "verification_signals",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("verification_check_id", sa.Integer(), nullable=False),
        sa.Column("signal_type", sa.String(length=64), nullable=False),
        sa.Column("signal_label", sa.Text(), nullable=False),
        sa.Column("signal_score", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(["verification_check_id"], ["verification_checks.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "lesson_certificates",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("certificate_id", sa.String(length=64), nullable=False),
        sa.Column("learner_name", sa.String(length=255), nullable=False),
        sa.Column("lesson_id", sa.String(length=64), nullable=False),
        sa.Column("lesson_title_en", sa.String(length=255), nullable=False),
        sa.Column("lesson_title_fr", sa.String(length=255), nullable=False),
        sa.Column("issued_on", sa.String(length=32), nullable=False),
        sa.Column("issuer", sa.String(length=255), nullable=False),
        sa.Column("founder", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("certificate_id"),
    )

    op.create_table(
        "incident_reports",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("verification_check_id", sa.Integer(), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("report_type", sa.String(length=64), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("reviewer_note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.String(length=64), nullable=False),
        sa.Column("updated_at", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["verification_check_id"], ["verification_checks.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_incident_reports_status", "incident_reports", ["status"])

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("actor_user_id", sa.Integer(), nullable=True),
        sa.Column("actor_role", sa.String(length=64), nullable=True),
        sa.Column("action", sa.String(length=128), nullable=False),
        sa.Column("resource_type", sa.String(length=64), nullable=True),
        sa.Column("resource_id", sa.String(length=128), nullable=True),
        sa.Column("outcome", sa.String(length=32), nullable=False),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.String(length=512), nullable=True),
        sa.Column("details_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])

    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token_hash", sa.String(length=128), nullable=False),
        sa.Column("expires_at", sa.String(length=64), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash", name="uq_refresh_token_hash"),
    )


def downgrade() -> None:
    op.drop_table("refresh_tokens")
    op.drop_index("ix_audit_logs_created_at", table_name="audit_logs")
    op.drop_index("ix_audit_logs_action", table_name="audit_logs")
    op.drop_table("audit_logs")
    op.drop_index("ix_incident_reports_status", table_name="incident_reports")
    op.drop_table("incident_reports")
    op.drop_table("lesson_certificates")
    op.drop_table("verification_signals")
    op.drop_index("ix_verification_checks_check_type", table_name="verification_checks")
    op.drop_table("verification_checks")
    op.drop_table("institutions")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
