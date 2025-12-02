"""add_must_change_password_to_users

Revision ID: 20251202_130000
Revises: 20251201_120000
Create Date: 2025-12-02 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20251202_130000'
down_revision: Union[str, None] = '20251201_120000'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add must_change_password column to users table"""
    op.add_column('users', sa.Column('must_change_password', sa.Boolean(), nullable=False, server_default='false'))


def downgrade() -> None:
    """Remove must_change_password column from users table"""
    op.drop_column('users', 'must_change_password')
