"""Add owner_id to ingested_payloads and quarantine ownerless legacy rows.

Existing rows have no owner. They keep owner_id NULL, which makes them readable
only by ADMIN accounts. Ownership is never auto-assigned to a user.

Revision ID: c20261101ingestowner
Revises: b20261023unique
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c20261101ingestowner"
down_revision: str | Sequence[str] | None = "b20261023unique"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "ingested_payloads",
        sa.Column("owner_id", sa.String(length=128), nullable=True),
    )
    op.create_index(
        "ix_ingested_payloads_owner_id",
        "ingested_payloads",
        ["owner_id"],
    )
    # Deliberately no UPDATE: legacy rows stay quarantined (owner_id IS NULL).


def downgrade() -> None:
    op.drop_index("ix_ingested_payloads_owner_id", table_name="ingested_payloads")
    op.drop_column("ingested_payloads", "owner_id")
