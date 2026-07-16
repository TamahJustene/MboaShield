"""Phase 4 analysis feedback labels for AI accuracy tracking.

Revision ID: 0003_phase4
Revises: 0002_phase2
Create Date: 2026-07-16
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0003_phase4"
down_revision = "0002_phase2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "analysis_feedback",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("verification_check_id", sa.Integer(), nullable=False),
        sa.Column("label", sa.String(length=64), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("actor_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(["verification_check_id"], ["verification_checks.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_analysis_feedback_verification_check_id", "analysis_feedback", ["verification_check_id"])
    op.create_index("ix_analysis_feedback_created_at", "analysis_feedback", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_analysis_feedback_created_at", table_name="analysis_feedback")
    op.drop_index("ix_analysis_feedback_verification_check_id", table_name="analysis_feedback")
    op.drop_table("analysis_feedback")
