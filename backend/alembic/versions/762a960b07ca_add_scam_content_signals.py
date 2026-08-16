"""add_scam_content_signals

Revision ID: 762a960b07ca
Revises: 4d6f5fb287b2
Create Date: 2026-08-15 00:00:00.000000

Stores the extension's page-content scam-phrase scan (extension/modules/scam_content_scanner.js)
on each scan record, matching network_signals/permission_signals — raw signals persisted for
dashboard display, and fed into the same log-odds fusion layer (ADR-014) via
backend/services/risk_fusion.py's scam_keyword_hits weight.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '762a960b07ca'
down_revision: Union[str, Sequence[str], None] = '4d6f5fb287b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('scans', sa.Column('scam_content_signals', postgresql.JSONB(astext_type=sa.Text()), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('scans', 'scam_content_signals')
