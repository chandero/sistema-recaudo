"""Add payment_agreements and agreement_installments tables

Revision ID: 006_payment_agreements
Revises: 005_process_notes
Create Date: 2026-08-25 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '006_payment_agreements'
down_revision: Union[str, None] = '005_process_notes'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'payment_agreements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('process_id', sa.Integer(), nullable=False),
        sa.Column('agreement_number', sa.String(length=100), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='PROPUESTA'),
        sa.Column('total_debt', sa.Float(), nullable=False, server_default='0'),
        sa.Column('total_agreed', sa.Float(), nullable=False, server_default='0'),
        sa.Column('interest_rate', sa.Float(), nullable=False, server_default='0'),
        sa.Column('installment_count', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('installment_amount', sa.Float(), nullable=False, server_default='0'),
        sa.Column('first_payment_date', sa.Date(), nullable=False),
        sa.Column('payment_day', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('grace_period_months', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('default_interest_rate', sa.Float(), nullable=False, server_default='0'),
        sa.Column('observations', sa.String(length=2000), nullable=True),
        sa.Column('accepted_at', sa.DateTime(), nullable=True),
        sa.Column('cancelled_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.ForeignKeyConstraint(['process_id'], ['cobro_processes.id']),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_payment_agreements_tenant_id'), 'payment_agreements', ['tenant_id'])
    op.create_index(op.f('ix_payment_agreements_process_id'), 'payment_agreements', ['process_id'])
    op.create_index(op.f('ix_payment_agreements_agreement_number'), 'payment_agreements', ['agreement_number'])

    op.create_table(
        'agreement_installments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('agreement_id', sa.Integer(), nullable=False),
        sa.Column('installment_number', sa.Integer(), nullable=False),
        sa.Column('due_date', sa.Date(), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('paid_amount', sa.Float(), nullable=False, server_default='0'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='PENDIENTE'),
        sa.Column('paid_at', sa.DateTime(), nullable=True),
        sa.Column('observations', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.ForeignKeyConstraint(['agreement_id'], ['payment_agreements.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_agreement_installments_tenant_id'), 'agreement_installments', ['tenant_id'])
    op.create_index(op.f('ix_agreement_installments_agreement_id'), 'agreement_installments', ['agreement_id'])


def downgrade() -> None:
    op.drop_index(op.f('ix_agreement_installments_agreement_id'), table_name='agreement_installments')
    op.drop_index(op.f('ix_agreement_installments_tenant_id'), table_name='agreement_installments')
    op.drop_table('agreement_installments')
    op.drop_index(op.f('ix_payment_agreements_agreement_number'), table_name='payment_agreements')
    op.drop_index(op.f('ix_payment_agreements_process_id'), table_name='payment_agreements')
    op.drop_index(op.f('ix_payment_agreements_tenant_id'), table_name='payment_agreements')
    op.drop_table('payment_agreements')
