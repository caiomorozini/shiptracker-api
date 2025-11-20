"""create_occurrence_codes_table

Revision ID: 20251120_120000
Revises: 20251118_065540
Create Date: 2025-11-20 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20251120_120000'
down_revision: Union[str, None] = '20251118_065540'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create occurrence_codes table"""
    op.create_table(
        'occurrence_codes',
        sa.Column('code', sa.String(length=10), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('process', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('code')
    )
    
    # Create indexes
    op.create_index(op.f('ix_occurrence_codes_code'), 'occurrence_codes', ['code'], unique=True)
    op.create_index(op.f('ix_occurrence_codes_type'), 'occurrence_codes', ['type'], unique=False)
    op.create_index(op.f('ix_occurrence_codes_process'), 'occurrence_codes', ['process'], unique=False)


def downgrade() -> None:
    """Drop occurrence_codes table"""
    op.drop_index(op.f('ix_occurrence_codes_process'), table_name='occurrence_codes')
    op.drop_index(op.f('ix_occurrence_codes_type'), table_name='occurrence_codes')
    op.drop_index(op.f('ix_occurrence_codes_code'), table_name='occurrence_codes')
    op.drop_table('occurrence_codes')
