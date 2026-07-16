"""Phase 7 National Trust Operations Center.

Revision ID: 0006_phase7
Revises: 0005_phase6
Create Date: 2026-07-16
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0006_phase7"
down_revision = "0005_phase6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "cases",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("priority", sa.String(length=32), nullable=False),
        sa.Column("region", sa.String(length=128), nullable=True),
        sa.Column("incident_id", sa.Integer(), nullable=True),
        sa.Column("verification_check_id", sa.Integer(), nullable=True),
        sa.Column("institution_id", sa.String(length=64), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("assigned_to_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.String(length=64), nullable=False),
        sa.Column("updated_at", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(["incident_id"], ["incident_reports.id"]),
        sa.ForeignKeyConstraint(["verification_check_id"], ["verification_checks.id"]),
        sa.ForeignKeyConstraint(["institution_id"], ["institutions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_cases_status", "cases", ["status"])
    op.create_index("ix_cases_incident_id", "cases", ["incident_id"])
    op.create_index("ix_cases_assigned_to_user_id", "cases", ["assigned_to_user_id"])

    op.create_table(
        "case_notes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("case_id", sa.Integer(), nullable=False),
        sa.Column("author_user_id", sa.Integer(), nullable=True),
        sa.Column("author_role", sa.String(length=64), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_case_notes_case_id", "case_notes", ["case_id"])

    op.create_table(
        "case_assignments",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("case_id", sa.Integer(), nullable=False),
        sa.Column("assignee_user_id", sa.Integer(), nullable=False),
        sa.Column("assigned_by_user_id", sa.Integer(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_case_assignments_case_id", "case_assignments", ["case_id"])
    op.create_index("ix_case_assignments_assignee_user_id", "case_assignments", ["assignee_user_id"])

    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("audience", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("resource_type", sa.String(length=64), nullable=True),
        sa.Column("resource_id", sa.String(length=128), nullable=True),
        sa.Column("read", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("webhook_delivered", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])
    op.create_index("ix_notifications_audience", "notifications", ["audience"])
    op.create_index("ix_notifications_created_at", "notifications", ["created_at"])

    op.create_table(
        "institution_health_snapshots",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("institution_id", sa.String(length=64), nullable=False),
        sa.Column("health_score", sa.Integer(), nullable=False),
        sa.Column("open_incidents", sa.Integer(), nullable=False),
        sa.Column("high_risk_checks", sa.Integer(), nullable=False),
        sa.Column("details_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(["institution_id"], ["institutions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_institution_health_snapshots_institution_id", "institution_health_snapshots", ["institution_id"])
    op.create_index("ix_institution_health_snapshots_created_at", "institution_health_snapshots", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_institution_health_snapshots_created_at", table_name="institution_health_snapshots")
    op.drop_index("ix_institution_health_snapshots_institution_id", table_name="institution_health_snapshots")
    op.drop_table("institution_health_snapshots")
    op.drop_index("ix_notifications_created_at", table_name="notifications")
    op.drop_index("ix_notifications_audience", table_name="notifications")
    op.drop_index("ix_notifications_user_id", table_name="notifications")
    op.drop_table("notifications")
    op.drop_index("ix_case_assignments_assignee_user_id", table_name="case_assignments")
    op.drop_index("ix_case_assignments_case_id", table_name="case_assignments")
    op.drop_table("case_assignments")
    op.drop_index("ix_case_notes_case_id", table_name="case_notes")
    op.drop_table("case_notes")
    op.drop_index("ix_cases_assigned_to_user_id", table_name="cases")
    op.drop_index("ix_cases_incident_id", table_name="cases")
    op.drop_index("ix_cases_status", table_name="cases")
    op.drop_table("cases")
