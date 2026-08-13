"""add_risk_pct

Revision ID: 33be02683ae4
Revises: ab476f0dcf44
Create Date: 2026-08-13 15:40:00.000000

ADR-015: risk_pct and confidence_pct are separate quantities. This column is backfilled from the
existing risk_score for any pre-existing rows before the NOT NULL constraint is applied, since
confidence_pct's historical values (round(risk_score * 100)) are exactly what risk_pct should have
been all along.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '33be02683ae4'
down_revision: Union[str, Sequence[str], None] = 'ab476f0dcf44'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('scans', sa.Column('risk_pct', sa.Integer(), nullable=True))
    op.execute("UPDATE scans SET risk_pct = ROUND(risk_score * 100) WHERE risk_pct IS NULL")
    op.alter_column('scans', 'risk_pct', nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('scans', 'risk_pct')
