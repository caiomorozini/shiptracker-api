"""add_timezone_to_datetime_columns

Adiciona suporte a timezone para todas as colunas datetime do banco de dados.
Configura o timezone para America/Sao_Paulo (horário de Brasília).

Revision ID: 20251120_180000
Revises: 20251120_170000
Create Date: 2025-11-20 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20251120_180000'
down_revision: Union[str, None] = '20251120_170000'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Altera todas as colunas TIMESTAMP para TIMESTAMP WITH TIME ZONE
    e define o timezone padrão do banco como America/Sao_Paulo
    """
    
    # Configurar timezone padrão do banco de dados
    op.execute("SET timezone = 'America/Sao_Paulo'")
    
    # Tabelas e suas colunas de timestamp
    tables_columns = {
        'users': ['created_at', 'updated_at', 'deleted_at'],
        'clients': ['created_at', 'updated_at', 'deleted_at'],
        'shipments': ['created_at', 'updated_at', 'deleted_at'],
        'shipment_tracking_events': ['created_at', 'updated_at', 'occurred_at'],
        'tracking_routines': ['created_at', 'updated_at', 'deleted_at', 'last_check_at'],
        'automations': ['created_at', 'updated_at', 'deleted_at'],
        'automation_executions': ['created_at', 'updated_at', 'executed_at'],
        'integrations': ['created_at', 'updated_at', 'deleted_at'],
        'audit_logs': ['created_at'],
        'notifications': ['created_at', 'updated_at', 'read_at'],
        'reports': ['created_at', 'updated_at', 'generated_at'],
        'client_interactions': ['created_at', 'updated_at', 'interaction_date'],
        'occurrence_codes': ['created_at', 'updated_at'],
    }
    
    # Alterar cada coluna para TIMESTAMPTZ
    for table_name, columns in tables_columns.items():
        for column_name in columns:
            # Verifica se a coluna existe antes de alterar
            op.execute(f"""
                DO $$
                BEGIN
                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name = '{table_name}' 
                        AND column_name = '{column_name}'
                    ) THEN
                        -- Altera para TIMESTAMP WITH TIME ZONE, convertendo valores existentes
                        ALTER TABLE {table_name} 
                        ALTER COLUMN {column_name} 
                        TYPE TIMESTAMP WITH TIME ZONE 
                        USING {column_name} AT TIME ZONE 'America/Sao_Paulo';
                    END IF;
                END $$;
            """)


def downgrade() -> None:
    """
    Reverte as colunas para TIMESTAMP sem timezone
    """
    
    tables_columns = {
        'users': ['created_at', 'updated_at', 'deleted_at'],
        'clients': ['created_at', 'updated_at', 'deleted_at'],
        'shipments': ['created_at', 'updated_at', 'deleted_at'],
        'shipment_tracking_events': ['created_at', 'updated_at', 'occurred_at'],
        'tracking_routines': ['created_at', 'updated_at', 'deleted_at', 'last_check_at'],
        'automations': ['created_at', 'updated_at', 'deleted_at'],
        'automation_executions': ['created_at', 'updated_at', 'executed_at'],
        'integrations': ['created_at', 'updated_at', 'deleted_at'],
        'audit_logs': ['created_at'],
        'notifications': ['created_at', 'updated_at', 'read_at'],
        'reports': ['created_at', 'updated_at', 'generated_at'],
        'client_interactions': ['created_at', 'updated_at', 'interaction_date'],
        'occurrence_codes': ['created_at', 'updated_at'],
    }
    
    # Reverte para TIMESTAMP sem timezone
    for table_name, columns in tables_columns.items():
        for column_name in columns:
            op.execute(f"""
                DO $$
                BEGIN
                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name = '{table_name}' 
                        AND column_name = '{column_name}'
                    ) THEN
                        ALTER TABLE {table_name} 
                        ALTER COLUMN {column_name} 
                        TYPE TIMESTAMP 
                        USING {column_name}::TIMESTAMP;
                    END IF;
                END $$;
            """)
