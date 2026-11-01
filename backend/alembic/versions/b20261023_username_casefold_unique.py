"""Enforce case-insensitive username uniqueness without renaming existing users.

Revision ID: b20261023unique
Revises: a9c3e1f5b7d2
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b20261023unique"
down_revision: str | Sequence[str] | None = "a9c3e1f5b7d2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    connection = op.get_bind()
    collisions = connection.execute(
        sa.text(
            "SELECT COUNT(*) FROM ("
            " SELECT lower(username) FROM users"
            " GROUP BY lower(username) HAVING COUNT(*) > 1"
            ") AS collisions"
        )
    ).scalar_one()
    if collisions:
        raise RuntimeError(
            "Cannot install unique case-insensitive username index: "
            "resolve legacy case-folded duplicates before upgrading."
        )
    op.create_index(
        "uq_users_username_lower",
        "users",
        [sa.text("lower(username)")],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("uq_users_username_lower", table_name="users")
