"""Phase T2 national digital trust network.

Revision ID: 0016_t2_trust_network
Revises: 0015_t1_trust
Create Date: 2026-07-17
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0016_t2_trust_network"
down_revision = "0015_t1_trust"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "trust_relationships",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("source_institution_id", sa.String(length=64), nullable=False),
        sa.Column("target_institution_id", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("policy_note", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.String(length=64), nullable=False),
        sa.Column("updated_at", sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "source_institution_id",
            "target_institution_id",
            name="uq_trust_relationship_pair",
        ),
    )
    op.create_index(
        "ix_trust_relationships_source_institution_id",
        "trust_relationships",
        ["source_institution_id"],
    )
    op.create_index(
        "ix_trust_relationships_target_institution_id",
        "trust_relationships",
        ["target_institution_id"],
    )
    op.create_index("ix_trust_relationships_status", "trust_relationships", ["status"])

    op.create_table(
        "exchange_channels",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("relationship_id", sa.Integer(), nullable=False),
        sa.Column("channel_type", sa.String(length=64), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("label", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("created_at", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(["relationship_id"], ["trust_relationships.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_exchange_channels_relationship_id", "exchange_channels", ["relationship_id"])
    op.create_index("ix_exchange_channels_channel_type", "exchange_channels", ["channel_type"])

    op.create_table(
        "shared_alerts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("alert_type", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("severity", sa.String(length=32), nullable=False, server_default="medium"),
        sa.Column("source_institution_id", sa.String(length=64), nullable=False),
        sa.Column("target_institutions_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("relationship_id", sa.Integer(), nullable=True),
        sa.Column("verification_check_id", sa.Integer(), nullable=True),
        sa.Column("trust_assessment_id", sa.Integer(), nullable=True),
        sa.Column("payload_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="shared"),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(["relationship_id"], ["trust_relationships.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_shared_alerts_alert_type", "shared_alerts", ["alert_type"])
    op.create_index(
        "ix_shared_alerts_source_institution_id",
        "shared_alerts",
        ["source_institution_id"],
    )
    op.create_index("ix_shared_alerts_severity", "shared_alerts", ["severity"])
    op.create_index("ix_shared_alerts_status", "shared_alerts", ["status"])
    op.create_index("ix_shared_alerts_relationship_id", "shared_alerts", ["relationship_id"])


def downgrade() -> None:
    op.drop_index("ix_shared_alerts_relationship_id", table_name="shared_alerts")
    op.drop_index("ix_shared_alerts_status", table_name="shared_alerts")
    op.drop_index("ix_shared_alerts_severity", table_name="shared_alerts")
    op.drop_index("ix_shared_alerts_source_institution_id", table_name="shared_alerts")
    op.drop_index("ix_shared_alerts_alert_type", table_name="shared_alerts")
    op.drop_table("shared_alerts")
    op.drop_index("ix_exchange_channels_channel_type", table_name="exchange_channels")
    op.drop_index("ix_exchange_channels_relationship_id", table_name="exchange_channels")
    op.drop_table("exchange_channels")
    op.drop_index("ix_trust_relationships_status", table_name="trust_relationships")
    op.drop_index("ix_trust_relationships_target_institution_id", table_name="trust_relationships")
    op.drop_index("ix_trust_relationships_source_institution_id", table_name="trust_relationships")
    op.drop_table("trust_relationships")
