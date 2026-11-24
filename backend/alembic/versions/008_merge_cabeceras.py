"""Merge de las dos cabeceras divergentes (user_tenants y notifications)

Las migraciones 005_user_tenants y 005_process_notes declararon como padre la misma
revisión d6276b05fcf1, lo que dejó el grafo Alembic con dos cabeceras simultáneas y
rompe "alembic upgrade head" con "Multiple head revisions are present".

Esta revisión une ambas ramas sin alterar las ya aplicadas en ninguna base: no toca
esquema, solo cierra el grafo. Después de aplicarla existe una única cabecera
008_merge_cabeceras.

Revision ID: 008_merge_cabeceras
Revises: 005_user_tenants, 007_notifications
Create Date: 2026-11-24 14:30:00.000000

"""
from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = '008_merge_cabeceras'
down_revision: Union[str, Sequence[str]] = ('005_user_tenants', '007_notifications')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Une ambos historiales: no hay cambios de esquema que aplicar."""


def downgrade() -> None:
    """Retroceder un merge no tiene sentido operativo; se deja explícitamente vacío."""
