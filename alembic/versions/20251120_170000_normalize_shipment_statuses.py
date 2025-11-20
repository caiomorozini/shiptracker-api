"""normalize_shipment_statuses

Normaliza os valores de status das encomendas para o padrão em inglês

Revision ID: 20251120_170000
Revises: 20251120_130000
Create Date: 2025-11-20 17:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20251120_170000'
down_revision: Union[str, None] = '20251120_130000'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Normalizar status existentes para o padrão em inglês"""
    
    # Mapeamento de status antigos para novos
    status_mapping = {
        # Português para inglês
        'aguardando': 'pending',
        'aguardando_postagem': 'pending',
        'postado': 'posted',
        'em_transito': 'in_transit',
        'em_trânsito': 'in_transit',
        'em_transito_para_a_unidade_destino': 'in_transit',
        'saiu_para_entrega': 'out_for_delivery',
        'entregue': 'delivered',
        'atrasado': 'delayed',
        'tentativa_falhou': 'failed_delivery',
        'devolvido': 'returned',
        'cancelado': 'cancelled',
        'retido': 'held',
        'aguardando_retirada': 'awaiting_pickup',
        
        # Casos em inglês que podem estar mal formatados
        'processing': 'posted',
        'shipped': 'posted',
        'transit': 'in_transit',
        'delivery': 'out_for_delivery',
        'complete': 'delivered',
        'failed': 'failed_delivery',
    }
    
    # Atualizar shipments
    for old_status, new_status in status_mapping.items():
        op.execute(
            f"""
            UPDATE shipments 
            SET status = '{new_status}' 
            WHERE status = '{old_status}'
            """
        )
    
    # Atualizar tracking events
    for old_status, new_status in status_mapping.items():
        op.execute(
            f"""
            UPDATE shipment_tracking_events 
            SET status = '{new_status}' 
            WHERE status = '{old_status}'
            """
        )
    
    print("✅ Status normalizados com sucesso!")


def downgrade() -> None:
    """Reverter normalização (não recomendado, pois perde informação)"""
    # Não reverter, pois os valores antigos eram inconsistentes
    pass
