"""Phase 8 threat intelligence (compliant sources).

Revision ID: 0007_phase8
Revises: 0006_phase7
Create Date: 2026-07-16
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0007_phase8"
down_revision = "0006_phase7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "intel_sources",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("source_class", sa.String(length=64), nullable=False),
        sa.Column("endpoint_url", sa.String(length=1024), nullable=False),
        sa.Column("egress_host", sa.String(length=255), nullable=False),
        sa.Column("tos_reference", sa.String(length=512), nullable=False),
        sa.Column("license", sa.String(length=255), nullable=False),
        sa.Column("auth_type", sa.String(length=32), nullable=False),
        sa.Column("credentials_json", sa.Text(), nullable=True),
        sa.Column("config_json", sa.Text(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("last_ingested_at", sa.String(length=64), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_intel_sources_source_class", "intel_sources", ["source_class"])

    op.create_table(
        "intel_items",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=False),
        sa.Column("external_id", sa.String(length=512), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("url", sa.String(length=1024), nullable=True),
        sa.Column("published_at", sa.String(length=64), nullable=True),
        sa.Column("content_hash", sa.String(length=128), nullable=False),
        sa.Column("handles_json", sa.Text(), nullable=False),
        sa.Column("urls_json", sa.Text(), nullable=False),
        sa.Column("raw_json", sa.Text(), nullable=True),
        sa.Column("campaign_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(["source_id"], ["intel_sources.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source_id", "external_id", name="uq_intel_item_source_external"),
    )
    op.create_index("ix_intel_items_source_id", "intel_items", ["source_id"])
    op.create_index("ix_intel_items_content_hash", "intel_items", ["content_hash"])
    op.create_index("ix_intel_items_campaign_id", "intel_items", ["campaign_id"])
    op.create_index("ix_intel_items_created_at", "intel_items", ["created_at"])

    op.create_table(
        "intel_campaigns",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("signal_count", sa.Integer(), nullable=False),
        sa.Column("shared_handles_json", sa.Text(), nullable=False),
        sa.Column("shared_urls_json", sa.Text(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("created_at", sa.String(length=64), nullable=False),
        sa.Column("updated_at", sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_intel_campaigns_status", "intel_campaigns", ["status"])

    op.create_table(
        "intel_correlations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("intel_item_id", sa.Integer(), nullable=False),
        sa.Column("incident_id", sa.Integer(), nullable=True),
        sa.Column("case_id", sa.Integer(), nullable=True),
        sa.Column("correlation_type", sa.String(length=64), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("details_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(["intel_item_id"], ["intel_items.id"]),
        sa.ForeignKeyConstraint(["incident_id"], ["incident_reports.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_intel_correlations_intel_item_id", "intel_correlations", ["intel_item_id"])
    op.create_index("ix_intel_correlations_incident_id", "intel_correlations", ["incident_id"])
    op.create_index("ix_intel_correlations_case_id", "intel_correlations", ["case_id"])


def downgrade() -> None:
    op.drop_index("ix_intel_correlations_case_id", table_name="intel_correlations")
    op.drop_index("ix_intel_correlations_incident_id", table_name="intel_correlations")
    op.drop_index("ix_intel_correlations_intel_item_id", table_name="intel_correlations")
    op.drop_table("intel_correlations")
    op.drop_index("ix_intel_campaigns_status", table_name="intel_campaigns")
    op.drop_table("intel_campaigns")
    op.drop_index("ix_intel_items_created_at", table_name="intel_items")
    op.drop_index("ix_intel_items_campaign_id", table_name="intel_items")
    op.drop_index("ix_intel_items_content_hash", table_name="intel_items")
    op.drop_index("ix_intel_items_source_id", table_name="intel_items")
    op.drop_table("intel_items")
    op.drop_index("ix_intel_sources_source_class", table_name="intel_sources")
    op.drop_table("intel_sources")
