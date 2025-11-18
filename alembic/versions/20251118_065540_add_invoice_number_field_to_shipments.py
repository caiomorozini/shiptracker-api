"""add_invoice_number_field_to_shipments

Revision ID: 20251118_065540
Revises:
Create Date: 2025-11-18 06:55:40.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20251118_065540'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add invoice_number and document fields, make tracking_code nullable"""
    # Make tracking_code nullable first
    op.alter_column('shipments', 'tracking_code',
                    existing_type=sa.String(length=100),
                    nullable=True)

    # Add invoice_number column as nullable first
    op.add_column('shipments', sa.Column('invoice_number', sa.String(length=100), nullable=True))

    # Add document column as nullable first
    op.add_column('shipments', sa.Column('document', sa.String(length=50), nullable=True))

    # Update existing records with default values
    op.execute("UPDATE shipments SET invoice_number = 'PENDING' WHERE invoice_number IS NULL")
    op.execute("UPDATE shipments SET document = '00000000000' WHERE document IS NULL")

    # Now make columns NOT NULL
    op.alter_column('shipments', 'invoice_number',
                    existing_type=sa.String(length=100),
                    nullable=False)
    op.alter_column('shipments', 'document',
                    existing_type=sa.String(length=50),
                    nullable=False)

    # Create indexes
    op.create_index(op.f('ix_shipments_invoice_number'), 'shipments', ['invoice_number'], unique=False)
    op.create_index(op.f('ix_shipments_document'), 'shipments', ['document'], unique=False)

    # Create composite index for document + invoice_number (for automation lookup)
    op.create_index('ix_shipments_document_invoice', 'shipments', ['document', 'invoice_number'], unique=False)


def downgrade() -> None:
    """Remove invoice_number and document fields, revert tracking_code to not nullable"""
    # Revert tracking_code to not nullable
    op.alter_column('shipments', 'tracking_code',
                    existing_type=sa.String(length=100),
                    nullable=False)

    # Remove composite index
    op.drop_index('ix_shipments_document_invoice', table_name='shipments')

    # Remove document column
    op.drop_index(op.f('ix_shipments_document'), table_name='shipments')
    op.drop_column('shipments', 'document')

    # Remove invoice_number column
    op.drop_index(op.f('ix_shipments_invoice_number'), table_name='shipments')
    op.drop_column('shipments', 'invoice_number')
