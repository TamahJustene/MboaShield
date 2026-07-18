"""Phase 12 advanced AI platform - model registry and evaluation.

Revision ID: 0012_phase12
Revises: 0010_phase11
Create Date: 2026-07-16
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0012_phase12"
down_revision = "0010_phase11"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ai_model_registry",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("model_id", sa.String(length=128), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("modality", sa.String(length=64), nullable=False),
        sa.Column("runtime", sa.String(length=64), nullable=False),
        sa.Column("checksum_sha256", sa.String(length=64), nullable=False),
        sa.Column("version", sa.String(length=32), nullable=False),
        sa.Column("config_json", sa.Text(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.String(length=64), nullable=False),
        sa.Column("updated_at", sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("model_id", name="uq_ai_model_id"),
    )
    op.create_index("ix_ai_model_registry_modality", "ai_model_registry", ["modality"])
    op.create_index("ix_ai_model_registry_runtime", "ai_model_registry", ["runtime"])

    op.create_table(
        "ai_evaluation_runs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("run_id", sa.String(length=64), nullable=False),
        sa.Column("dataset", sa.String(length=64), nullable=False),
        sa.Column("metrics_json", sa.Text(), nullable=False),
        sa.Column("latency_ms_p50", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("run_id"),
    )
    op.create_index("ix_ai_evaluation_runs_dataset", "ai_evaluation_runs", ["dataset"])
    op.create_index("ix_ai_evaluation_runs_created_at", "ai_evaluation_runs", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_ai_evaluation_runs_created_at", table_name="ai_evaluation_runs")
    op.drop_index("ix_ai_evaluation_runs_dataset", table_name="ai_evaluation_runs")
    op.drop_table("ai_evaluation_runs")
    op.drop_index("ix_ai_model_registry_runtime", table_name="ai_model_registry")
    op.drop_index("ix_ai_model_registry_modality", table_name="ai_model_registry")
    op.drop_table("ai_model_registry")
