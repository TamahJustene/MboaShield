"""Phase 2 national incident workflow fields and event timeline.

Revision ID: 0002_phase2
Revises: 0001_phase1
Create Date: 2026-07-16
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0002_phase2"
down_revision = "0001_phase1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("incident_reports") as batch:
        batch.add_column(sa.Column("priority", sa.String(length=32), nullable=False, server_default="normal"))
        batch.add_column(sa.Column("region", sa.String(length=128), nullable=True))
        batch.add_column(sa.Column("assigned_to_user_id", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("institution_id", sa.String(length=64), nullable=True))
        batch.add_column(sa.Column("decision_summary", sa.Text(), nullable=True))
        batch.add_column(sa.Column("public_advisory", sa.Text(), nullable=True))
        batch.add_column(sa.Column("ai_summary_json", sa.Text(), nullable=True))

    op.create_table(
        "incident_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("incident_id", sa.Integer(), nullable=False),
        sa.Column("from_status", sa.String(length=32), nullable=True),
        sa.Column("to_status", sa.String(length=32), nullable=False),
        sa.Column("actor_user_id", sa.Integer(), nullable=True),
        sa.Column("actor_role", sa.String(length=64), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("details_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(["incident_id"], ["incident_reports.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_incident_events_incident_id", "incident_events", ["incident_id"])
    op.create_index("ix_incident_events_created_at", "incident_events", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_incident_events_created_at", table_name="incident_events")
    op.drop_index("ix_incident_events_incident_id", table_name="incident_events")
    op.drop_table("incident_events")
    with op.batch_alter_table("incident_reports") as batch:
        batch.drop_column("ai_summary_json")
        batch.drop_column("public_advisory")
        batch.drop_column("decision_summary")
        batch.drop_column("institution_id")
        batch.drop_column("assigned_to_user_id")
        batch.drop_column("region")
        batch.drop_column("priority")
