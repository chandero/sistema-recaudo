"""Add action column to generated_documents

Revision ID: 010_historial_generacion
Revises: 009_fechas_documentos
Create Date: 2026-11-25 15:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '010_historial_generacion'
down_revision: Union[str, None] = '009_fechas_documentos'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Traza de la operación que produjo el archivo: documento oficial, impresión por
    # rango, lote de correspondencia o exportación a Excel. Sin ella, el histórico no
    # permite saber qué se entregó cuando se imprimió un rango completo.
    op.add_column(
        'generated_documents',
        sa.Column(
            'action',
            sa.String(length=40),
            nullable=True,
            # Backfill: los registros previos quedan como documento oficial, igual que
            # los deja run_migrations.py al añadir la columna en producción.
            server_default='documento',
        )
    )


def downgrade() -> None:
    op.drop_column('generated_documents', 'action')
