"""add_client_id

Revision ID: 4d6f5fb287b2
Revises: 33be02683ae4
Create Date: 2026-08-15 00:00:00.000000

Per-browser-install identifier so /history and /stats can be scoped to the browser that produced
each scan, instead of showing every scan ever recorded to every dashboard visitor. Nullable:
existing rows predate the extension generating a client_id and simply won't appear in any
client-scoped view (they were never attributable to one browser anyway).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '4d6f5fb287b2'
down_revision: Union[str, Sequence[str], None] = '33be02683ae4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('scans', sa.Column('client_id', sa.String(length=64), nullable=True))
    op.create_index(op.f('ix_scans_client_id'), 'scans', ['client_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_scans_client_id'), table_name='scans')
    op.drop_column('scans', 'client_id')
