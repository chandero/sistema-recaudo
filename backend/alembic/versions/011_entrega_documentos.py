"""Add recipient and delivery columns to generated_documents

Revision ID: 011_entrega_documentos
Revises: 010_historial_generacion
Create Date: 2026-11-25 17:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '011_entrega_documentos'
down_revision: Union[str, None] = '010_historial_generacion'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # El histórico guardaba el correo solo si el envío resultó exitoso (is_sent), y aun
    # así se perdía la dirección cuando el funcionario la digitó a mano. Estas dos columnas
    # dejan constancia del destinatario real y de por qué el archivo salió (o no) del sistema.
    op.add_column(
        'generated_documents',
        sa.Column('recipient_email', sa.String(length=255), nullable=True)
    )
    op.add_column(
        'generated_documents',
        sa.Column('delivery_method', sa.String(length=40), nullable=True)
    )


def downgrade() -> None:
    op.drop_column('generated_documents', 'delivery_method')
    op.drop_column('generated_documents', 'recipient_email')
