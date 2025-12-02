"""add_seller_role_and_seller_id_to_shipments

Revision ID: 20251201_120000
Revises: 20251201_110000
Create Date: 2025-12-01 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20251201_120000'
down_revision: Union[str, None] = '20251201_110000'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add seller role to UserRole enum and seller_id to shipments table"""
    
    # Step 1: Add 'SELLER' to the UserRole enum (uppercase to match existing pattern)
    # PostgreSQL requires explicit type modification for enums
    op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'SELLER'")
    
    # Step 2: Add seller_id column to shipments table
    op.add_column('shipments', sa.Column('seller_id', sa.UUID(), nullable=True))
    
    # Step 3: Add foreign key constraint
    op.create_foreign_key(
        'fk_shipments_seller_id_users',
        'shipments',
        'users',
        ['seller_id'],
        ['id'],
        ondelete='SET NULL'
    )
    
    # Step 4: Add index for better query performance
    op.create_index('ix_shipments_seller_id', 'shipments', ['seller_id'])


def downgrade() -> None:
    """Remove seller_id from shipments and seller role from UserRole enum"""
    
    # Step 1: Drop index
    op.drop_index('ix_shipments_seller_id', table_name='shipments')
    
    # Step 2: Drop foreign key constraint
    op.drop_constraint('fk_shipments_seller_id_users', 'shipments', type_='foreignkey')
    
    # Step 3: Drop seller_id column
    op.drop_column('shipments', 'seller_id')
    
    # Note: Removing enum values in PostgreSQL is complex and requires recreating the enum
    # For safety, we'll leave the 'seller' value in the enum during downgrade
    # If you need to remove it completely, you'll need to recreate the entire enum type
