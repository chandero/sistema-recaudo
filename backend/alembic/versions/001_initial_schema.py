"""Initial database schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2024-07-02 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Crear tabla tenants
    op.create_table('tenants',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=True, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code')
    )

    # Crear tabla users
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=True, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )

    # Crear tabla clients
    op.create_table('clients',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('identification', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('address', sa.String(length=500), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=True, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'identification', name='uq_tenant_identification')
    )

    # Crear tabla workflow_states
    op.create_table('workflow_states',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=True),
        sa.Column('code', sa.String(length=100), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('order', sa.Integer(), nullable=True),
        sa.Column('max_days', sa.Integer(), nullable=True),
        sa.Column('is_final', sa.Boolean(), nullable=True, default=False),
        sa.Column('active', sa.Boolean(), nullable=True, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'code', name='uq_tenant_workflow_code')
    )

    # Crear tabla processes
    op.create_table('processes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('client_id', sa.Integer(), nullable=False),
        sa.Column('current_state_id', sa.Integer(), nullable=False),
        sa.Column('reference', sa.String(length=100), nullable=True),
        sa.Column('total_amount', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('paid_amount', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('resolution_number', sa.String(length=50), nullable=True),
        sa.Column('radicado_number', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ),
        sa.ForeignKeyConstraint(['current_state_id'], ['workflow_states.id'], ),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Crear tabla obligations
    op.create_table('obligations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('process_id', sa.Integer(), nullable=False),
        sa.Column('number', sa.String(length=100), nullable=False),
        sa.Column('vigencia', sa.String(length=20), nullable=True),
        sa.Column('capital', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('interests', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('total', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['process_id'], ['processes.id'], ),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Crear tabla documents
    op.create_table('documents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('process_id', sa.Integer(), nullable=True),
        sa.Column('template_id', sa.Integer(), nullable=True),
        sa.Column('document_type', sa.String(length=50), nullable=False),
        sa.Column('file_name', sa.String(length=255), nullable=True),
        sa.Column('file_path', sa.String(length=500), nullable=True),
        sa.Column('generated_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['process_id'], ['processes.id'], ),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Crear tabla document_templates
    op.create_table('document_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('template_type', sa.String(length=50), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=True),
        sa.Column('variables_schema', sa.Text(), nullable=True),
        sa.Column('version', sa.Integer(), nullable=True, default=1),
        sa.Column('active', sa.Boolean(), nullable=True, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'code', name='uq_tenant_template_code')
    )

    # Crear tabla process_history
    op.create_table('process_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('process_id', sa.Integer(), nullable=False),
        sa.Column('from_state_id', sa.Integer(), nullable=True),
        sa.Column('to_state_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('observation', sa.Text(), nullable=True),
        sa.Column('automatic', sa.Boolean(), nullable=True, default=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['from_state_id'], ['workflow_states.id'], ),
        sa.ForeignKeyConstraint(['process_id'], ['processes.id'], ),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.ForeignKeyConstraint(['to_state_id'], ['workflow_states.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Crear tabla tasks
    op.create_table('tasks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('process_id', sa.Integer(), nullable=True),
        sa.Column('assigned_to', sa.Integer(), nullable=True),
        sa.Column('assigned_role', sa.String(length=50), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True, default='pending'),
        sa.Column('due_date', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['assigned_to'], ['users.id'], ),
        sa.ForeignKeyConstraint(['process_id'], ['processes.id'], ),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Crear tabla import_templates
    op.create_table('import_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('column_mappings', sa.Text(), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=True, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Crear índices
    op.create_index('ix_users_tenant_id', 'users', ['tenant_id'])
    op.create_index('ix_clients_tenant_id', 'clients', ['tenant_id'])
    op.create_index('ix_processes_tenant_id', 'processes', ['tenant_id'])
    op.create_index('ix_processes_client_id', 'processes', ['client_id'])
    op.create_index('ix_processes_current_state_id', 'processes', ['current_state_id'])
    op.create_index('ix_workflow_states_tenant_id', 'workflow_states', ['tenant_id'])
    op.create_index('ix_obligations_tenant_id', 'obligations', ['tenant_id'])
    op.create_index('ix_obligations_process_id', 'obligations', ['process_id'])
    op.create_index('ix_documents_tenant_id', 'documents', ['tenant_id'])
    op.create_index('ix_documents_process_id', 'documents', ['process_id'])
    op.create_index('ix_document_templates_tenant_id', 'document_templates', ['tenant_id'])
    op.create_index('ix_process_history_tenant_id', 'process_history', ['tenant_id'])
    op.create_index('ix_process_history_process_id', 'process_history', ['process_id'])
    op.create_index('ix_tasks_tenant_id', 'tasks', ['tenant_id'])
    op.create_index('ix_tasks_process_id', 'tasks', ['process_id'])
    op.create_index('ix_import_templates_tenant_id', 'import_templates', ['tenant_id'])


def downgrade() -> None:
    # Eliminar índices
    op.drop_index('ix_import_templates_tenant_id', table_name='import_templates')
    op.drop_index('ix_tasks_process_id', table_name='tasks')
    op.drop_index('ix_tasks_tenant_id', table_name='tasks')
    op.drop_index('ix_process_history_process_id', table_name='process_history')
    op.drop_index('ix_process_history_tenant_id', table_name='process_history')
    op.drop_index('ix_document_templates_tenant_id', table_name='document_templates')
    op.drop_index('ix_documents_process_id', table_name='documents')
    op.drop_index('ix_documents_tenant_id', table_name='documents')
    op.drop_index('ix_obligations_process_id', table_name='obligations')
    op.drop_index('ix_obligations_tenant_id', table_name='obligations')
    op.drop_index('ix_workflow_states_tenant_id', table_name='workflow_states')
    op.drop_index('ix_processes_current_state_id', table_name='processes')
    op.drop_index('ix_processes_client_id', table_name='processes')
    op.drop_index('ix_processes_tenant_id', table_name='processes')
    op.drop_index('ix_clients_tenant_id', table_name='clients')
    op.drop_index('ix_users_tenant_id', table_name='users')

    # Eliminar tablas en orden inverso
    op.drop_table('import_templates')
    op.drop_table('tasks')
    op.drop_table('process_history')
    op.drop_table('document_templates')
    op.drop_table('documents')
    op.drop_table('obligations')
    op.drop_table('processes')
    op.drop_table('workflow_states')
    op.drop_table('clients')
    op.drop_table('users')
    op.drop_table('tenants')
