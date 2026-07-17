"""Phase 14 governance - consent, risk register, model/dataset cards, controls.

Revision ID: 0014_phase14
Revises: 0012_phase12
Create Date: 2026-07-16
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0014_phase14"
down_revision = "0012_phase12"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "consent_records",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("subject_key", sa.String(length=128), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("feature", sa.String(length=64), nullable=False),
        sa.Column("granted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("purpose", sa.String(length=255), nullable=False),
        sa.Column("policy_version", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.String(length=64), nullable=False),
        sa.Column("updated_at", sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("subject_key", "feature", name="uq_consent_subject_feature"),
    )
    op.create_index("ix_consent_records_subject_key", "consent_records", ["subject_key"])
    op.create_index("ix_consent_records_feature", "consent_records", ["feature"])
    op.create_index("ix_consent_records_user_id", "consent_records", ["user_id"])

    op.create_table(
        "risk_register",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("risk_id", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("threat_model_ref", sa.String(length=128), nullable=False),
        sa.Column("likelihood", sa.String(length=32), nullable=False),
        sa.Column("impact", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("owner", sa.String(length=128), nullable=False),
        sa.Column("mitigation", sa.Text(), nullable=False),
        sa.Column("residual_risk", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.String(length=64), nullable=False),
        sa.Column("updated_at", sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("risk_id", name="uq_risk_id"),
    )
    op.create_index("ix_risk_register_category", "risk_register", ["category"])
    op.create_index("ix_risk_register_status", "risk_register", ["status"])
    op.create_index("ix_risk_register_threat_model_ref", "risk_register", ["threat_model_ref"])

    op.create_table(
        "model_cards",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("card_id", sa.String(length=128), nullable=False),
        sa.Column("model_id", sa.String(length=128), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("version", sa.String(length=32), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("intended_use", sa.Text(), nullable=False),
        sa.Column("limitations", sa.Text(), nullable=False),
        sa.Column("certainty_policy", sa.String(length=64), nullable=False),
        sa.Column("body_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.String(length=64), nullable=False),
        sa.Column("updated_at", sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("card_id", name="uq_model_card_id"),
    )
    op.create_index("ix_model_cards_model_id", "model_cards", ["model_id"])

    op.create_table(
        "dataset_cards",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("card_id", sa.String(length=128), nullable=False),
        sa.Column("dataset_id", sa.String(length=128), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("version", sa.String(length=32), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("provenance", sa.Text(), nullable=False),
        sa.Column("languages", sa.String(length=64), nullable=False),
        sa.Column("body_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.String(length=64), nullable=False),
        sa.Column("updated_at", sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("card_id", name="uq_dataset_card_id"),
    )
    op.create_index("ix_dataset_cards_dataset_id", "dataset_cards", ["dataset_id"])

    op.create_table(
        "governance_controls",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("control_id", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("evidence", sa.Text(), nullable=False),
        sa.Column("created_at", sa.String(length=64), nullable=False),
        sa.Column("updated_at", sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("control_id", name="uq_governance_control_id"),
    )
    op.create_index("ix_governance_controls_category", "governance_controls", ["category"])
    op.create_index("ix_governance_controls_status", "governance_controls", ["status"])


def downgrade() -> None:
    op.drop_index("ix_governance_controls_status", table_name="governance_controls")
    op.drop_index("ix_governance_controls_category", table_name="governance_controls")
    op.drop_table("governance_controls")
    op.drop_index("ix_dataset_cards_dataset_id", table_name="dataset_cards")
    op.drop_table("dataset_cards")
    op.drop_index("ix_model_cards_model_id", table_name="model_cards")
    op.drop_table("model_cards")
    op.drop_index("ix_risk_register_threat_model_ref", table_name="risk_register")
    op.drop_index("ix_risk_register_status", table_name="risk_register")
    op.drop_index("ix_risk_register_category", table_name="risk_register")
    op.drop_table("risk_register")
    op.drop_index("ix_consent_records_user_id", table_name="consent_records")
    op.drop_index("ix_consent_records_feature", table_name="consent_records")
    op.drop_index("ix_consent_records_subject_key", table_name="consent_records")
    op.drop_table("consent_records")
