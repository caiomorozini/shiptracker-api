"""add_feedback_table

Cria a tabela de feedback para bug reports e sugestões de funcionalidades.

Revision ID: 20251201_110000
Revises: 20251201_100000
Create Date: 2025-12-01 11:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20251201_110000'
down_revision: Union[str, None] = '20251201_100000'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'feedback',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('type', sa.String(20), nullable=False, index=True),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='open', index=True),
        sa.Column('priority', sa.String(20), nullable=True),
        sa.Column('votes', sa.Integer, nullable=False, server_default='0'),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
    )
    
    # Índices para performance
    op.create_index('ix_feedback_type_status', 'feedback', ['type', 'status'])
    op.create_index('ix_feedback_votes', 'feedback', ['votes'])
    op.create_index('ix_feedback_created_at', 'feedback', ['created_at'])


def downgrade() -> None:
    op.drop_index('ix_feedback_created_at', table_name='feedback')
    op.drop_index('ix_feedback_votes', table_name='feedback')
    op.drop_index('ix_feedback_type_status', table_name='feedback')
    op.drop_table('feedback')
