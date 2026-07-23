"""Add city and department fields to tenant

Revision ID: d6276b05fcf1
Revises: 003_user_invitations
Create Date: 2026-07-23 11:09:23.698939

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd6276b05fcf1'
down_revision: Union[str, None] = '003_user_invitations'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add city column to tenants table
    op.add_column('tenants', sa.Column('city', sa.String(length=100), nullable=True))
    # Add department column to tenants table
    op.add_column('tenants', sa.Column('department', sa.String(length=100), nullable=True))


def downgrade() -> None:
    # Drop department column from tenants table
    op.drop_column('tenants', 'department')
    # Drop city column from tenants table
    op.drop_column('tenants', 'city')
