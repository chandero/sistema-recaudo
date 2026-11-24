"""Add user_tenants many-to-many table

Revision ID: 005_user_tenants
Revises: d6276b05fcf1
Create Date: 2026-08-24
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "005_user_tenants"
down_revision: Union[str, None] = "d6276b05fcf1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_tenants",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=False, server_default="OPERATOR"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "tenant_id"),
    )
    op.create_index("ix_user_tenants_user_id", "user_tenants", ["user_id"])
    op.create_index("ix_user_tenants_tenant_id", "user_tenants", ["tenant_id"])

    # Migrate existing user.tenant_id data into user_tenants
    op.execute(
        "INSERT INTO user_tenants (user_id, tenant_id, role, created_at) "
        "SELECT id, tenant_id, role, created_at FROM users WHERE tenant_id IS NOT NULL"
    )


def downgrade() -> None:
    op.drop_index("ix_user_tenants_tenant_id", table_name="user_tenants")
    op.drop_index("ix_user_tenants_user_id", table_name="user_tenants")
    op.drop_table("user_tenants")
