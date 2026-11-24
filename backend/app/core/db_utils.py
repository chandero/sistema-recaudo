"""Utilidades de base de datos compatibles con SQLite y PostgreSQL."""
from sqlalchemy import func


def days_since(column):
    """Devuelve una expresión SQL que calcula días transcurridos desde `column` hasta ahora.
    Compatible con SQLite (julianday) y PostgreSQL (EXTRACT EPOCH)."""
    from app.core.database import is_postgres
    now = func.now()
    if is_postgres:
        # PostgreSQL: EXTRACT(EPOCH FROM (now - column)) / 86400
        return func.extract('epoch', now - column) / 86400.0
    else:
        # SQLite: julianday(now) - julianday(column)
        return func.julianday(now) - func.julianday(column)
