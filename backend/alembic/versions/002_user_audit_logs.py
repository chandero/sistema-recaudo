"""Add user management audit log

Revision ID: 002_user_audit_logs
Revises: 001_initial_schema
Create Date: 2026-07-15
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "002_user_audit_logs"
down_revision: Union[str, None] = "001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_audit_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=True),
        sa.Column("actor_user_id", sa.Integer(), nullable=False),
        sa.Column("target_user_id", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(length=50), nullable=False),
        sa.Column("changes", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["target_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_user_audit_logs_tenant_id", "user_audit_logs", ["tenant_id"])
    op.create_index("ix_user_audit_logs_actor_user_id", "user_audit_logs", ["actor_user_id"])
    op.create_index("ix_user_audit_logs_target_user_id", "user_audit_logs", ["target_user_id"])
    op.create_index("ix_user_audit_logs_action", "user_audit_logs", ["action"])
    op.create_index("ix_user_audit_logs_created_at", "user_audit_logs", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_user_audit_logs_created_at", table_name="user_audit_logs")
    op.drop_index("ix_user_audit_logs_action", table_name="user_audit_logs")
    op.drop_index("ix_user_audit_logs_target_user_id", table_name="user_audit_logs")
    op.drop_index("ix_user_audit_logs_actor_user_id", table_name="user_audit_logs")
    op.drop_index("ix_user_audit_logs_tenant_id", table_name="user_audit_logs")
    op.drop_table("user_audit_logs")
