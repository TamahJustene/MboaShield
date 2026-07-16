"""Phase 9 Digital Evidence Vault.

Revision ID: 0008_phase9
Revises: 0007_phase8
Create Date: 2026-07-16
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0008_phase9"
down_revision = "0007_phase8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "evidence_items",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("evidence_id", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("content_type", sa.String(length=128), nullable=False),
        sa.Column("filename", sa.String(length=512), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("storage_backend", sa.String(length=32), nullable=False),
        sa.Column("storage_key", sa.String(length=1024), nullable=False),
        sa.Column("case_id", sa.Integer(), nullable=True),
        sa.Column("incident_id", sa.Integer(), nullable=True),
        sa.Column("verification_check_id", sa.Integer(), nullable=True),
        sa.Column("custodian_user_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("retention_until", sa.String(length=64), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.String(length=64), nullable=False),
        sa.Column("updated_at", sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("evidence_id", name="uq_evidence_public_id"),
    )
    op.create_index("ix_evidence_items_evidence_id", "evidence_items", ["evidence_id"])
    op.create_index("ix_evidence_items_sha256", "evidence_items", ["sha256"])
    op.create_index("ix_evidence_items_case_id", "evidence_items", ["case_id"])
    op.create_index("ix_evidence_items_incident_id", "evidence_items", ["incident_id"])
    op.create_index("ix_evidence_items_status", "evidence_items", ["status"])
    op.create_index("ix_evidence_items_retention_until", "evidence_items", ["retention_until"])
    op.create_index("ix_evidence_items_custodian_user_id", "evidence_items", ["custodian_user_id"])

    op.create_table(
        "evidence_custody_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("evidence_id", sa.String(length=64), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("from_user_id", sa.Integer(), nullable=True),
        sa.Column("to_user_id", sa.Integer(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("details_json", sa.Text(), nullable=True),
        sa.Column("event_hash", sa.String(length=128), nullable=False),
        sa.Column("prev_event_hash", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_evidence_custody_events_evidence_id", "evidence_custody_events", ["evidence_id"])
    op.create_index("ix_evidence_custody_events_event_type", "evidence_custody_events", ["event_type"])
    op.create_index("ix_evidence_custody_events_created_at", "evidence_custody_events", ["created_at"])

    op.create_table(
        "evidence_exports",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("export_id", sa.String(length=64), nullable=False),
        sa.Column("evidence_id", sa.String(length=64), nullable=False),
        sa.Column("format", sa.String(length=32), nullable=False),
        sa.Column("package_sha256", sa.String(length=64), nullable=False),
        sa.Column("signature", sa.String(length=128), nullable=False),
        sa.Column("storage_key", sa.String(length=1024), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("export_id"),
    )
    op.create_index("ix_evidence_exports_export_id", "evidence_exports", ["export_id"])
    op.create_index("ix_evidence_exports_evidence_id", "evidence_exports", ["evidence_id"])


def downgrade() -> None:
    op.drop_index("ix_evidence_exports_evidence_id", table_name="evidence_exports")
    op.drop_index("ix_evidence_exports_export_id", table_name="evidence_exports")
    op.drop_table("evidence_exports")
    op.drop_index("ix_evidence_custody_events_created_at", table_name="evidence_custody_events")
    op.drop_index("ix_evidence_custody_events_event_type", table_name="evidence_custody_events")
    op.drop_index("ix_evidence_custody_events_evidence_id", table_name="evidence_custody_events")
    op.drop_table("evidence_custody_events")
    op.drop_index("ix_evidence_items_custodian_user_id", table_name="evidence_items")
    op.drop_index("ix_evidence_items_retention_until", table_name="evidence_items")
    op.drop_index("ix_evidence_items_status", table_name="evidence_items")
    op.drop_index("ix_evidence_items_incident_id", table_name="evidence_items")
    op.drop_index("ix_evidence_items_case_id", table_name="evidence_items")
    op.drop_index("ix_evidence_items_sha256", table_name="evidence_items")
    op.drop_index("ix_evidence_items_evidence_id", table_name="evidence_items")
    op.drop_table("evidence_items")
