"""add_occurrence_code_to_tracking_events

Revision ID: 20251120_130000
Revises: 20251120_120000
Create Date: 2025-11-20 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20251120_130000'
down_revision: Union[str, None] = '20251120_120000'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add occurrence_code, unit and protocol fields to shipment_tracking_events"""
    
    # Add occurrence_code column with foreign key
    op.add_column('shipment_tracking_events', 
                  sa.Column('occurrence_code', sa.String(length=10), nullable=True))
    
    # Add unit column (location unit)
    op.add_column('shipment_tracking_events', 
                  sa.Column('unit', sa.String(length=255), nullable=True))
    
    # Add protocol column (SEFAZ protocol)
    op.add_column('shipment_tracking_events', 
                  sa.Column('protocol', sa.String(length=100), nullable=True))
    
    # Create foreign key constraint
    op.create_foreign_key(
        'fk_tracking_events_occurrence_code',
        'shipment_tracking_events', 
        'occurrence_codes',
        ['occurrence_code'], 
        ['code'],
        ondelete='SET NULL'
    )
    
    # Create index on occurrence_code
    op.create_index(
        op.f('ix_shipment_tracking_events_occurrence_code'), 
        'shipment_tracking_events', 
        ['occurrence_code'], 
        unique=False
    )


def downgrade() -> None:
    """Remove occurrence_code, unit and protocol fields from shipment_tracking_events"""
    
    # Drop index
    op.drop_index(op.f('ix_shipment_tracking_events_occurrence_code'), 
                  table_name='shipment_tracking_events')
    
    # Drop foreign key
    op.drop_constraint('fk_tracking_events_occurrence_code', 
                      'shipment_tracking_events', 
                      type_='foreignkey')
    
    # Drop columns
    op.drop_column('shipment_tracking_events', 'protocol')
    op.drop_column('shipment_tracking_events', 'unit')
    op.drop_column('shipment_tracking_events', 'occurrence_code')
