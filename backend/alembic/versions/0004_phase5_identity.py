"""Phase 5 hardened identity: MFA fields and partner API keys.

Revision ID: 0004_phase5
Revises: 0003_phase4
Create Date: 2026-07-16
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0004_phase5"
down_revision = "0003_phase4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("users") as batch:
        batch.add_column(sa.Column("mfa_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")))
        batch.add_column(sa.Column("mfa_secret", sa.String(length=255), nullable=True))
        batch.add_column(sa.Column("oidc_subject", sa.String(length=255), nullable=True))
        batch.add_column(sa.Column("oidc_provider", sa.String(length=64), nullable=True))
    op.create_index("ix_users_oidc_subject", "users", ["oidc_subject"])

    op.create_table(
        "partner_api_keys",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("partner_org", sa.String(length=255), nullable=False),
        sa.Column("key_prefix", sa.String(length=32), nullable=False),
        sa.Column("key_hash", sa.String(length=128), nullable=False),
        sa.Column("scopes_json", sa.Text(), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("revoked", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("expires_at", sa.String(length=64), nullable=True),
        sa.Column("last_used_at", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key_hash", name="uq_partner_api_key_hash"),
    )
    op.create_index("ix_partner_api_keys_key_prefix", "partner_api_keys", ["key_prefix"])


def downgrade() -> None:
    op.drop_index("ix_partner_api_keys_key_prefix", table_name="partner_api_keys")
    op.drop_table("partner_api_keys")
    op.drop_index("ix_users_oidc_subject", table_name="users")
    with op.batch_alter_table("users") as batch:
        batch.drop_column("oidc_provider")
        batch.drop_column("oidc_subject")
        batch.drop_column("mfa_secret")
        batch.drop_column("mfa_enabled")
