"""Phase 10 Institution Administration Platform.

Revision ID: 0009_phase10
Revises: 0008_phase9
Create Date: 2026-07-16
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0009_phase10"
down_revision = "0008_phase9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("institutions") as batch:
        batch.add_column(sa.Column("branding_json", sa.Text(), nullable=False, server_default="{}"))
        batch.add_column(sa.Column("contact_email", sa.String(length=255), nullable=True))

    op.create_table(
        "institution_domains",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("institution_id", sa.String(length=64), nullable=False),
        sa.Column("domain", sa.String(length=255), nullable=False),
        sa.Column("verification_token", sa.String(length=128), nullable=False),
        sa.Column("verification_method", sa.String(length=64), nullable=False),
        sa.Column("verified", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("verified_at", sa.String(length=64), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(["institution_id"], ["institutions.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("institution_id", "domain", name="uq_institution_domain"),
    )
    op.create_index("ix_institution_domains_institution_id", "institution_domains", ["institution_id"])
    op.create_index("ix_institution_domains_domain", "institution_domains", ["domain"])

    op.create_table(
        "institution_memberships",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("institution_id", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("member_role", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("invited_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.String(length=64), nullable=False),
        sa.Column("updated_at", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(["institution_id"], ["institutions.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("institution_id", "user_id", name="uq_institution_membership"),
    )
    op.create_index("ix_institution_memberships_institution_id", "institution_memberships", ["institution_id"])
    op.create_index("ix_institution_memberships_user_id", "institution_memberships", ["user_id"])
    op.create_index("ix_institution_memberships_status", "institution_memberships", ["status"])

    op.create_table(
        "institution_official_accounts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("institution_id", sa.String(length=64), nullable=False),
        sa.Column("platform", sa.String(length=64), nullable=False),
        sa.Column("handle", sa.String(length=255), nullable=False),
        sa.Column("url", sa.String(length=1024), nullable=True),
        sa.Column("verified", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(["institution_id"], ["institutions.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("institution_id", "platform", "handle", name="uq_institution_official_account"),
    )
    op.create_index(
        "ix_institution_official_accounts_institution_id",
        "institution_official_accounts",
        ["institution_id"],
    )

    op.create_table(
        "institution_api_keys",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("institution_id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("key_prefix", sa.String(length=32), nullable=False),
        sa.Column("key_hash", sa.String(length=128), nullable=False),
        sa.Column("scopes_json", sa.Text(), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("revoked", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("expires_at", sa.String(length=64), nullable=True),
        sa.Column("last_used_at", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(["institution_id"], ["institutions.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key_hash"),
    )
    op.create_index("ix_institution_api_keys_institution_id", "institution_api_keys", ["institution_id"])


def downgrade() -> None:
    op.drop_index("ix_institution_api_keys_institution_id", table_name="institution_api_keys")
    op.drop_table("institution_api_keys")
    op.drop_index("ix_institution_official_accounts_institution_id", table_name="institution_official_accounts")
    op.drop_table("institution_official_accounts")
    op.drop_index("ix_institution_memberships_status", table_name="institution_memberships")
    op.drop_index("ix_institution_memberships_user_id", table_name="institution_memberships")
    op.drop_index("ix_institution_memberships_institution_id", table_name="institution_memberships")
    op.drop_table("institution_memberships")
    op.drop_index("ix_institution_domains_domain", table_name="institution_domains")
    op.drop_index("ix_institution_domains_institution_id", table_name="institution_domains")
    op.drop_table("institution_domains")
    with op.batch_alter_table("institutions") as batch:
        batch.drop_column("contact_email")
        batch.drop_column("branding_json")
