"""add_last_scanned_at

Revision ID: f48ff135cc1a
Revises: 762a960b07ca
Create Date: 2026-08-15 00:00:00.000000

Scans move from append-only to upsert-by-(client_id, url): re-analyzing an already-scanned URL now
updates that row instead of inserting a new one, so `/history` needs a mutable "when was this last
checked" column separate from the immutable `created_at`. Backfilled from created_at for existing
rows, since every existing row's only scan so far *is* its most recent one.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'f48ff135cc1a'
down_revision: Union[str, Sequence[str], None] = '762a960b07ca'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('scans', sa.Column('last_scanned_at', sa.DateTime(timezone=True), nullable=True))
    op.execute("UPDATE scans SET last_scanned_at = created_at WHERE last_scanned_at IS NULL")
    op.alter_column('scans', 'last_scanned_at', nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('scans', 'last_scanned_at')
