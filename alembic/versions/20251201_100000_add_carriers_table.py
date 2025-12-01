"""add_carriers_table

Cria a tabela de transportadoras (carriers) para padronizar o cadastro de empresas de transporte.

Revision ID: 20251201_100000
Revises: 20251120_180000
Create Date: 2025-12-01 10:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20251201_100000'
down_revision: Union[str, None] = '20251120_180000'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Cria a tabela carriers e insere as transportadoras padrão
    """
    # Criar tabela carriers
    op.create_table(
        'carriers',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False, unique=True, index=True),
        sa.Column('code', sa.String(50), nullable=False, unique=True, index=True),
        sa.Column('color', sa.String(20), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    
    # Inserir transportadoras padrão
    op.execute("""
        INSERT INTO carriers (id, name, code, color, active, is_default, created_at, updated_at)
        VALUES 
            (gen_random_uuid(), 'SSW', 'ssw', '#FF6B35', true, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
            (gen_random_uuid(), 'Correios', 'correios', '#FFCC00', true, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
            (gen_random_uuid(), 'SEDEX', 'sedex', '#003DA5', true, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
            (gen_random_uuid(), 'Jadlog', 'jadlog', '#1E90FF', true, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
            (gen_random_uuid(), 'Loggi', 'loggi', '#FF6B00', true, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
    """)


def downgrade() -> None:
    """
    Remove a tabela carriers
    """
    op.drop_table('carriers')
