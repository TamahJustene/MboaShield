"""Phase 11 verified government communications.

Revision ID: 0010_phase11
Revises: 0009_phase10
Create Date: 2026-07-16
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0010_phase11"
down_revision = "0009_phase10"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "government_announcements",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("announcement_id", sa.String(length=64), nullable=False),
        sa.Column("institution_id", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("current_version", sa.Integer(), nullable=False),
        sa.Column("locale", sa.String(length=16), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("published_by_user_id", sa.Integer(), nullable=True),
        sa.Column("published_at", sa.String(length=64), nullable=True),
        sa.Column("revoked_at", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.String(length=64), nullable=False),
        sa.Column("updated_at", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(["institution_id"], ["institutions.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("announcement_id", name="uq_government_announcement_id"),
    )
    op.create_index("ix_government_announcements_announcement_id", "government_announcements", ["announcement_id"])
    op.create_index("ix_government_announcements_institution_id", "government_announcements", ["institution_id"])
    op.create_index("ix_government_announcements_status", "government_announcements", ["status"])

    op.create_table(
        "announcement_versions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("announcement_id", sa.String(length=64), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("signature", sa.String(length=128), nullable=False),
        sa.Column("signing_kid", sa.String(length=64), nullable=False),
        sa.Column("published_at", sa.String(length=64), nullable=False),
        sa.Column("published_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("announcement_id", "version_number", name="uq_announcement_version"),
    )
    op.create_index("ix_announcement_versions_announcement_id", "announcement_versions", ["announcement_id"])


def downgrade() -> None:
    op.drop_index("ix_announcement_versions_announcement_id", table_name="announcement_versions")
    op.drop_table("announcement_versions")
    op.drop_index("ix_government_announcements_status", table_name="government_announcements")
    op.drop_index("ix_government_announcements_institution_id", table_name="government_announcements")
    op.drop_index("ix_government_announcements_announcement_id", table_name="government_announcements")
    op.drop_table("government_announcements")
