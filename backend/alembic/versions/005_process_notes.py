"""Add process_notes table

Revision ID: 005_process_notes
Revises: 004_tenant_process_configs
Create Date: 2026-08-24 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '005_process_notes'
down_revision: Union[str, None] = '004_tenant_process_configs'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'process_notes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('process_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('note_type', sa.String(length=50), nullable=False, server_default='general'),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('content', sa.String(length=5000), nullable=False),
        sa.Column('is_pinned', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.ForeignKeyConstraint(['process_id'], ['cobro_processes.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_process_notes_tenant_id'), 'process_notes', ['tenant_id'])
    op.create_index(op.f('ix_process_notes_process_id'), 'process_notes', ['process_id'])
    op.create_index(op.f('ix_process_notes_note_type'), 'process_notes', ['note_type'])


def downgrade() -> None:
    op.drop_index(op.f('ix_process_notes_note_type'), table_name='process_notes')
    op.drop_index(op.f('ix_process_notes_process_id'), table_name='process_notes')
    op.drop_index(op.f('ix_process_notes_tenant_id'), table_name='process_notes')
    op.drop_table('process_notes')
