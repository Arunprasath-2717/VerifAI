"""create_token_usages_table

Revision ID: f8b2c4d6e8a0
Revises: e7a1b2c3d4e5
Create Date: 2026-10-19 21:45:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import app.models.base


# revision identifiers, used by Alembic.
revision: str = "f8b2c4d6e8a0"
down_revision: Union[str, Sequence[str], None] = "e7a1b2c3d4e5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema to include token_usages table."""
    op.create_table(
        "token_usages",
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("verification_id", app.models.base.GUID(), nullable=True),
        sa.Column("owner_id", sa.String(length=128), nullable=False),
        sa.Column("operation", sa.String(length=64), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("model_name", sa.String(length=128), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("output_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "is_estimated",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "estimated_cost_usd", sa.Float(), nullable=False, server_default="0.0"
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["verification_id"], ["verifications.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_token_usages_verification_id"),
        "token_usages",
        ["verification_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_token_usages_owner_id"), "token_usages", ["owner_id"], unique=False
    )
    op.create_index(
        "ix_token_usages_owner_created",
        "token_usages",
        ["owner_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_token_usages_verif_op",
        "token_usages",
        ["verification_id", "operation"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema to drop token_usages table."""
    op.drop_index("ix_token_usages_verif_op", table_name="token_usages")
    op.drop_index("ix_token_usages_owner_created", table_name="token_usages")
    op.drop_index(op.f("ix_token_usages_owner_id"), table_name="token_usages")
    op.drop_index(op.f("ix_token_usages_verification_id"), table_name="token_usages")
    op.drop_table("token_usages")
