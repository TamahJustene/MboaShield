"""Phase T1 national trust assessments.

Revision ID: 0015_t1_trust
Revises: 0014_phase14
Create Date: 2026-07-17
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0015_t1_trust"
down_revision = "0014_phase14"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "trust_assessments",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("object_type", sa.String(length=64), nullable=False),
        sa.Column("object_id", sa.String(length=128), nullable=True),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("band", sa.String(length=32), nullable=False),
        sa.Column("certainty", sa.String(length=32), nullable=False, server_default="none"),
        sa.Column("signals_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("evidence_refs_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("verification_check_id", sa.Integer(), nullable=True),
        sa.Column("payload_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("input_lang", sa.String(length=16), nullable=False, server_default="en"),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["verification_check_id"], ["verification_checks.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_trust_assessments_object_type", "trust_assessments", ["object_type"])
    op.create_index("ix_trust_assessments_object_id", "trust_assessments", ["object_id"])
    op.create_index(
        "ix_trust_assessments_verification_check_id",
        "trust_assessments",
        ["verification_check_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_trust_assessments_verification_check_id", table_name="trust_assessments")
    op.drop_index("ix_trust_assessments_object_id", table_name="trust_assessments")
    op.drop_index("ix_trust_assessments_object_type", table_name="trust_assessments")
    op.drop_table("trust_assessments")
