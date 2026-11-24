"""Add paid_date, notification_date and executory_date to obligations

Revision ID: 009_fechas_documentos
Revises: 008_merge_cabeceras
Create Date: 2026-11-24 10:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '009_fechas_documentos'
down_revision: Union[str, None] = '008_merge_cabeceras'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # paid_date: fecha de pago total que exige el Auto de Archivo. Si está
    # vacía, el generador la deriva del historial del proceso.
    op.add_column(
        'obligations',
        sa.Column('paid_date', sa.Date(), nullable=True)
    )
    # notification_date: fecha de notificación del acto administrativo,
    # insumo de la Constancia Secretarial.
    op.add_column(
        'obligations',
        sa.Column('notification_date', sa.Date(), nullable=True)
    )
    # executory_date: fecha desde la cual quedó ejecutoriada la resolución,
    # que la Constancia Secretarial declara antes de remitir a cobro coactivo.
    op.add_column(
        'obligations',
        sa.Column('executory_date', sa.Date(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column('obligations', 'executory_date')
    op.drop_column('obligations', 'notification_date')
    op.drop_column('obligations', 'paid_date')
