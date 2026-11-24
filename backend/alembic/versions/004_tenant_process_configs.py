"""Add tenant_process_configs table

Revision ID: 004_tenant_process_configs
Revises: d6276b05fcf1
Create Date: 2026-08-23 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '004_tenant_process_configs'
down_revision: Union[str, None] = 'd6276b05fcf1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('tenant_process_configs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('prefijo_resolucion', sa.String(length=50), nullable=True, server_default='RES-2024'),
        sa.Column('numero_inicial', sa.Integer(), nullable=True, server_default='1000'),
        sa.Column('numero_actual', sa.Integer(), nullable=True, server_default='1000'),
        sa.Column('prefijo_radicado', sa.String(length=50), nullable=True, server_default='RAD-2024'),
        sa.Column('radicado_inicial', sa.Integer(), nullable=True, server_default='5000'),
        sa.Column('radicado_actual', sa.Integer(), nullable=True, server_default='5000'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id')
    )
    op.create_index('ix_tenant_process_configs_tenant_id', 'tenant_process_configs', ['tenant_id'])


def downgrade() -> None:
    op.drop_index('ix_tenant_process_configs_tenant_id', table_name='tenant_process_configs')
    op.drop_table('tenant_process_configs')
