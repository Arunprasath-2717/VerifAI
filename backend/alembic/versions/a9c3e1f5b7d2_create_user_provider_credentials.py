"""create_user_provider_credentials_table

Revision ID: a9c3e1f5b7d2
Revises: f8b2c4d6e8a0
Create Date: 2026-10-20 10:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

import app.models.base

# revision identifiers, used by Alembic.
revision: str = "a9c3e1f5b7d2"
down_revision: str | Sequence[str] | None = "f8b2c4d6e8a0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create encrypted per-user provider credential storage."""
    op.create_table(
        "user_provider_credentials",
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("user_id", app.models.base.GUID(), nullable=False),
        sa.Column("provider_id", sa.String(length=64), nullable=False),
        sa.Column("encrypted_api_key", sa.Text(), nullable=False),
        sa.Column("key_hint", sa.String(length=32), nullable=False),
        sa.Column("base_url", sa.String(length=512), nullable=True),
        sa.Column("organization_id", sa.String(length=128), nullable=True),
        sa.Column("last_validated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "validation_status",
            sa.String(length=32),
            nullable=False,
            server_default="NOT_TESTED",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id", "provider_id", name="uq_user_provider_credential"
        ),
    )
    op.create_index(
        op.f("ix_user_provider_credentials_user_id"),
        "user_provider_credentials",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "ix_user_provider_credentials_user",
        "user_provider_credentials",
        ["user_id", "provider_id"],
        unique=False,
    )


def downgrade() -> None:
    """Drop encrypted provider credential storage."""
    op.drop_index(
        "ix_user_provider_credentials_user", table_name="user_provider_credentials"
    )
    op.drop_index(
        op.f("ix_user_provider_credentials_user_id"),
        table_name="user_provider_credentials",
    )
    op.drop_table("user_provider_credentials")
