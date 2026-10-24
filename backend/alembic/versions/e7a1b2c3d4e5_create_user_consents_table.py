"""create_user_consents_table

Revision ID: e7a1b2c3d4e5
Revises: d57e9de0b8e6
Create Date: 2026-10-10 09:12:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import app.models.base


# revision identifiers, used by Alembic.
revision: str = 'e7a1b2c3d4e5'
down_revision: Union[str, Sequence[str], None] = 'd57e9de0b8e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema to include user_consents table."""
    op.create_table(
        'user_consents',
        sa.Column('id', app.models.base.GUID(), nullable=False),
        sa.Column('user_id', app.models.base.GUID(), nullable=False),
        sa.Column('terms_version', sa.String(length=32), nullable=False),
        sa.Column('privacy_version', sa.String(length=32), nullable=False),
        sa.Column('consented_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('action_source', sa.String(length=64), nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=512), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_consents_user_id'), 'user_consents', ['user_id'], unique=False)
    op.create_index('ix_user_consents_user_consented', 'user_consents', ['user_id', 'consented_at'], unique=False)
    op.create_index('ix_user_consents_versions', 'user_consents', ['terms_version', 'privacy_version'], unique=False)


def downgrade() -> None:
    """Downgrade schema removing user_consents table."""
    op.drop_index('ix_user_consents_versions', table_name='user_consents')
    op.drop_index('ix_user_consents_user_consented', table_name='user_consents')
    op.drop_index(op.f('ix_user_consents_user_id'), table_name='user_consents')
    op.drop_table('user_consents')
